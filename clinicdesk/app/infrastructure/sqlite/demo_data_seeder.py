from __future__ import annotations

import sqlite3
import random
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from clinicdesk.app.application.demo_data.dtos import (
    AppointmentCreateDTO,
    DoctorCreateDTO,
    IncidenceDTO,
    PatientCreateDTO,
    PersonalCreateDTO,
)
from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Medico, Paciente, Personal, Sala
from clinicdesk.app.infrastructure.sqlite.repos_medicos import MedicosRepository
from clinicdesk.app.infrastructure.sqlite.repos_pacientes import PacientesRepository
from clinicdesk.app.infrastructure.sqlite.repos_personal import PersonalRepository
from clinicdesk.app.infrastructure.sqlite.repos_salas import SalasRepository

LOGGER = get_logger(__name__)


@dataclass(slots=True)
class DemoSeedPersistResult:
    doctors: int
    patients: int
    personal: int
    appointments: int
    incidences: int
    medicamentos: int
    materiales: int
    recetas: int
    receta_lineas: int
    dispensaciones: int
    movimientos_medicamentos: int
    movimientos_materiales: int
    turnos: int
    ausencias: int


@dataclass(slots=True)
class _BatchProgress:
    phase: str
    total_items: int
    total_batches: int
    started_at: datetime

    def log_batch(self, batch_index: int, done: int) -> None:
        elapsed_s = max((datetime.now(UTC) - self.started_at).total_seconds(), 1e-6)
        rate = done / elapsed_s
        pending = max(0, self.total_items - done)
        eta_s = pending / rate if rate > 0 else 0.0
        LOGGER.info(
            "seed_progress",
            extra={
                "phase": self.phase,
                "batch_index": batch_index,
                "batch_total": self.total_batches,
                "done": done,
                "total": self.total_items,
                "elapsed_s": round(elapsed_s, 2),
                "rate": round(rate, 2),
                "eta_s": round(eta_s, 2),
            },
        )


class DemoDataSeeder:
    def __init__(
        self,
        connection: sqlite3.Connection,
        medicos_repo: MedicosRepository | None = None,
        pacientes_repo: PacientesRepository | None = None,
        personal_repo: PersonalRepository | None = None,
        salas_repo: SalasRepository | None = None,
    ) -> None:
        self._connection = connection
        self._medicos_repo = medicos_repo or MedicosRepository(connection)
        self._pacientes_repo = pacientes_repo or PacientesRepository(connection)
        self._personal_repo = personal_repo or PersonalRepository(connection)
        self._salas_repo = salas_repo or SalasRepository(connection)

    def persist(
        self,
        doctors: list[DoctorCreateDTO],
        patients: list[PatientCreateDTO],
        staff: list[PersonalCreateDTO],
        appointments: list[AppointmentCreateDTO],
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        *,
        seed: int = 123,
        from_date: date | None = None,
        to_date: date | None = None,
        n_medicamentos: int = 200,
        n_materiales: int = 120,
        n_recetas: int = 400,
        n_movimientos: int = 2000,
        turns_months: int = 2,
        n_ausencias: int = 60,
        batch_size: int = 500,
    ) -> DemoSeedPersistResult:
        safe_batch_size = max(1, batch_size)
        from_date = from_date or (date.today() - timedelta(days=30))
        to_date = to_date or date.today()
        LOGGER.info("Persisting doctors... count=%s", len(doctors))
        doctor_ids = [self._medicos_repo.create(_to_medico(dto)) for dto in doctors]
        LOGGER.info("Persisting patients... count=%s", len(patients))
        patient_ids = [self._pacientes_repo.create(_to_paciente(dto)) for dto in patients]
        LOGGER.info("Persisting staff... count=%s", len(staff))
        staff_ids = [self._personal_repo.create(_to_personal(dto)) for dto in staff]
        sala_ids = self._ensure_salas()
        appointment_id_map = self._persist_appointments(
            appointments,
            patient_ids,
            doctor_ids,
            sala_ids,
            batch_size=safe_batch_size,
        )
        incidences_count = self._persist_incidences(
            incidences_by_appointment,
            appointment_id_map,
            staff_ids,
            batch_size=safe_batch_size,
        )
        meds_count, mat_count = self._seed_inventory(n_medicamentos, n_materiales)
        recipes_count, line_count, disp_count = self._seed_recetas_dispensaciones(
            patient_ids,
            doctor_ids,
            staff_ids,
            n_recetas,
            seed,
            from_date,
            to_date,
        )
        mov_med, mov_mat = self._seed_movimientos(n_movimientos, staff_ids, seed, recipes_count > 0)
        turnos_count = self._seed_turnos_y_calendario(doctor_ids, staff_ids, turns_months)
        ausencias_count = self._seed_ausencias(doctor_ids, staff_ids, n_ausencias, seed)
        return DemoSeedPersistResult(
            doctors=len(doctor_ids),
            patients=len(patient_ids),
            personal=len(staff_ids),
            appointments=len(appointment_id_map),
            incidences=incidences_count,
            medicamentos=meds_count,
            materiales=mat_count,
            recetas=recipes_count,
            receta_lineas=line_count,
            dispensaciones=disp_count,
            movimientos_medicamentos=mov_med,
            movimientos_materiales=mov_mat,
            turnos=turnos_count,
            ausencias=ausencias_count,
        )

    def _seed_inventory(self, n_meds: int, n_materials: int) -> tuple[int, int]:
        meds = max(1, n_meds)
        materials = max(1, n_materials)
        for idx in range(meds):
            self._connection.execute(
                """INSERT INTO medicamentos (nombre_compuesto, nombre_comercial, cantidad_en_almacen, activo)
                VALUES (?, ?, ?, 1)""",
                (f"Compuesto {idx:03d}", f"Medicamento {idx:03d}", 20 + (idx % 200)),
            )
        for idx in range(materials):
            self._connection.execute(
                """INSERT INTO materiales (nombre, fungible, cantidad_en_almacen, activo)
                VALUES (?, ?, ?, 1)""",
                (f"Material {idx:03d}", 1 if idx % 3 else 0, 10 + (idx % 120)),
            )
        self._connection.commit()
        return meds, materials

    def _seed_recetas_dispensaciones(
        self,
        patient_ids: list[int],
        doctor_ids: list[int],
        staff_ids: list[int],
        n_recetas: int,
        seed: int,
        from_date: date,
        to_date: date,
    ) -> tuple[int, int, int]:
        med_ids = [r[0] for r in self._connection.execute("SELECT id FROM medicamentos WHERE activo = 1").fetchall()]
        if not med_ids:
            return 0, 0, 0
        rng = random.Random(seed + 7000)
        recipes = max(1, n_recetas)
        total_lineas = 0
        total_disp = 0
        for idx in range(recipes):
            d = from_date + timedelta(days=rng.randint(0, max((to_date - from_date).days, 1)))
            receta_cur = self._connection.execute(
                """INSERT INTO recetas (paciente_id, medico_id, fecha, observaciones, estado, activo)
                VALUES (?, ?, ?, ?, 'ACTIVA', 1)""",
                (patient_ids[idx % len(patient_ids)], doctor_ids[idx % len(doctor_ids)], f"{d.isoformat()} 10:00:00", "Receta demo"),
            )
            receta_id = int(receta_cur.lastrowid)
            for line_idx in range(rng.randint(1, 5)):
                cantidad = rng.randint(1, 4)
                pendiente = rng.randint(0, cantidad)
                linea_cur = self._connection.execute(
                    """INSERT INTO receta_lineas (receta_id, medicamento_id, dosis, duracion_dias, instrucciones,
                    cantidad, pendiente, estado, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                    (receta_id, med_ids[(idx + line_idx) % len(med_ids)], "1 cada 8h", 7 + line_idx, "Tras comida", cantidad, pendiente, "PENDIENTE" if pendiente else "DISPENSADA"),
                )
                total_lineas += 1
                if staff_ids:
                    disp_fecha = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 20))
                    self._connection.execute(
                        """INSERT INTO dispensaciones (receta_id, receta_linea_id, medicamento_id, personal_id, fecha_hora,
                        cantidad, observaciones, activo)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                        (receta_id, int(linea_cur.lastrowid), med_ids[(idx + line_idx) % len(med_ids)], staff_ids[(idx + line_idx) % len(staff_ids)], disp_fecha.isoformat(sep=" ", timespec="seconds"), max(1, cantidad - pendiente), "Dispensación demo"),
                    )
                    total_disp += 1
        self._connection.commit()
        return recipes, total_lineas, total_disp

    def _seed_movimientos(self, n_movimientos: int, staff_ids: list[int], seed: int, has_recetas: bool) -> tuple[int, int]:
        rng = random.Random(seed + 8000)
        med_ids = [r[0] for r in self._connection.execute("SELECT id FROM medicamentos WHERE activo = 1").fetchall()]
        mat_ids = [r[0] for r in self._connection.execute("SELECT id FROM materiales WHERE activo = 1").fetchall()]
        total_med = max(1, n_movimientos // 2)
        total_mat = max(1, n_movimientos - total_med)
        for idx in range(total_med):
            ts = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 40))
            self._connection.execute(
                """INSERT INTO movimientos_medicamentos (medicamento_id, fecha_hora, tipo, cantidad, motivo, personal_id, referencia, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (med_ids[idx % len(med_ids)], ts.isoformat(sep=" ", timespec="seconds"), "ENTRADA" if idx % 5 else "SALIDA", rng.randint(1, 20), "Movimiento demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, "seed-demo" if has_recetas else "seed"),
            )
        for idx in range(total_mat):
            ts = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 40))
            self._connection.execute(
                """INSERT INTO movimientos_materiales (material_id, fecha_hora, tipo, cantidad, motivo, personal_id, referencia, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (mat_ids[idx % len(mat_ids)], ts.isoformat(sep=" ", timespec="seconds"), "ENTRADA" if idx % 4 else "SALIDA", rng.randint(1, 15), "Movimiento demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, "seed-demo"),
            )
        self._connection.commit()
        return total_med, total_mat

    def _seed_turnos_y_calendario(self, doctor_ids: list[int], staff_ids: list[int], months: int) -> int:
        defaults = [("Mañana", "08:00", "14:00"), ("Tarde", "14:00", "20:00")]
        turnos_ids: list[int] = []
        for nombre, ini, fin in defaults:
            cur = self._connection.execute("INSERT OR IGNORE INTO turnos (nombre, hora_inicio, hora_fin, activo) VALUES (?, ?, ?, 1)", (nombre, ini, fin))
            if cur.lastrowid:
                turnos_ids.append(int(cur.lastrowid))
        if not turnos_ids:
            turnos_ids = [r[0] for r in self._connection.execute("SELECT id FROM turnos WHERE activo = 1").fetchall()]
        start = date.today().replace(day=1)
        days = max(30, months * 30)
        for offset in range(days):
            d = start + timedelta(days=offset)
            for mid in doctor_ids:
                self._connection.execute("INSERT OR IGNORE INTO calendario_medico (medico_id, fecha, turno_id, activo) VALUES (?, ?, ?, 1)", (mid, d.isoformat(), turnos_ids[(mid + offset) % len(turnos_ids)]))
            for pid in staff_ids:
                self._connection.execute("INSERT OR IGNORE INTO calendario_personal (personal_id, fecha, turno_id, activo) VALUES (?, ?, ?, 1)", (pid, d.isoformat(), turnos_ids[(pid + offset) % len(turnos_ids)]))
        self._connection.commit()
        return len(turnos_ids)

    def _seed_ausencias(self, doctor_ids: list[int], staff_ids: list[int], total: int, seed: int) -> int:
        rng = random.Random(seed + 9000)
        tipos = ["VACACIONES", "BAJA", "DIA_SUELTO"]
        created = 0
        for idx in range(max(1, total // 2)):
            ini = datetime.now().date() + timedelta(days=rng.randint(-20, 20))
            fin = ini + timedelta(days=rng.randint(0, 5))
            self._connection.execute(
                "INSERT INTO ausencias_medico (medico_id, inicio, fin, tipo, motivo, aprobado_por_personal_id, creado_en, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                (doctor_ids[idx % len(doctor_ids)], ini.isoformat(), fin.isoformat(), tipos[idx % len(tipos)], "Ausencia demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, datetime.now().isoformat(sep=" ", timespec="seconds")),
            )
            created += 1
        for idx in range(max(1, total - created)):
            ini = datetime.now().date() + timedelta(days=rng.randint(-20, 20))
            fin = ini + timedelta(days=rng.randint(0, 3))
            self._connection.execute(
                "INSERT INTO ausencias_personal (personal_id, inicio, fin, tipo, motivo, aprobado_por_personal_id, creado_en, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
                (staff_ids[idx % len(staff_ids)], ini.isoformat(), fin.isoformat(), tipos[(idx + 1) % len(tipos)], "Ausencia demo", staff_ids[(idx + 1) % len(staff_ids)] if staff_ids else None, datetime.now().isoformat(sep=" ", timespec="seconds")),
            )
            created += 1
        self._connection.commit()
        return created

    def _ensure_salas(self) -> list[int]:
        rooms = self._salas_repo.list_all(solo_activas=True)
        if rooms:
            return [room.id for room in rooms if room.id is not None]
        defaults = [
            Sala(nombre="Consulta Demo 1", tipo=TipoSala.CONSULTA, ubicacion="Planta 1", activa=True),
            Sala(nombre="Consulta Demo 2", tipo=TipoSala.CONSULTA, ubicacion="Planta 1", activa=True),
            Sala(nombre="Box Demo", tipo=TipoSala.FISIOTERAPIA, ubicacion="Planta 2", activa=True),
        ]
        return [self._salas_repo.create(room) for room in defaults]

    def _persist_appointments(
        self,
        appointments: list[AppointmentCreateDTO],
        patient_ids: list[int],
        doctor_ids: list[int],
        room_ids: list[int],
        *,
        batch_size: int,
    ) -> dict[str, int]:
        appointment_id_map: dict[str, int] = {}
        total = len(appointments)
        if total == 0:
            return appointment_id_map
        total_batches = (total + batch_size - 1) // batch_size
        tracker = _BatchProgress("persist_appointments", total, total_batches, datetime.now(UTC))
        for batch_index, batch in enumerate(_iter_batches(appointments, batch_size), start=1):
            for dto in batch:
                cur = self._connection.execute(
                    """
                    INSERT INTO citas (
                        paciente_id, medico_id, sala_id, inicio, fin, estado, motivo, notas
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        patient_ids[dto.patient_index],
                        doctor_ids[dto.doctor_index],
                        room_ids[(dto.patient_index + dto.doctor_index) % len(room_ids)],
                        dto.starts_at,
                        dto.ends_at,
                        dto.status,
                        dto.reason,
                        dto.notes,
                    ),
                )
                appointment_id_map[dto.external_id] = int(cur.lastrowid)
            self._connection.commit()
            tracker.log_batch(batch_index, len(appointment_id_map))
        return appointment_id_map

    def _persist_incidences(
        self,
        incidences_by_appointment: dict[str, list[IncidenceDTO]],
        appointment_ids: dict[str, int],
        staff_ids: list[int],
        *,
        batch_size: int,
    ) -> int:
        if not staff_ids:
            return 0
        total = 0
        flattened: list[tuple[int, IncidenceDTO]] = []
        for external_id, entries in incidences_by_appointment.items():
            cita_id = appointment_ids.get(external_id)
            if cita_id is None:
                continue
            for entry in entries:
                flattened.append((cita_id, entry))
        total_rows = len(flattened)
        if total_rows == 0:
            return 0
        total_batches = (total_rows + batch_size - 1) // batch_size
        tracker = _BatchProgress("persist_incidences", total_rows, total_batches, datetime.now(UTC))
        for batch_index, batch in enumerate(_iter_batches(flattened, batch_size), start=1):
            for cita_id, entry in batch:
                confirmer_id = staff_ids[cita_id % len(staff_ids)]
                self._connection.execute(
                    """
                    INSERT INTO incidencias (
                        tipo, severidad, estado, fecha_hora, descripcion,
                        cita_id, confirmado_por_personal_id, nota_override
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry.incidence_type,
                        entry.severity,
                        entry.status,
                        entry.occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
                        entry.description,
                        cita_id,
                        confirmer_id,
                        entry.override_note or "seed-demo",
                    ),
                )
                total += 1
            self._connection.commit()
            tracker.log_batch(batch_index, total)
        return total


def _iter_batches(items: list, batch_size: int):
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def _to_medico(dto: DoctorCreateDTO) -> Medico:
    return Medico(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        num_colegiado=dto.collegiate_number,
        especialidad=dto.specialty,
    )


def _to_paciente(dto: PatientCreateDTO) -> Paciente:
    return Paciente(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        alergias=dto.allergies,
        observaciones=dto.observations,
    )


def _to_personal(dto: PersonalCreateDTO) -> Personal:
    return Personal(
        tipo_documento=TipoDocumento(dto.document_type),
        documento=dto.document,
        nombre=dto.first_name,
        apellidos=dto.last_name,
        telefono=dto.phone,
        email=dto.email,
        fecha_nacimiento=dto.birth_date,
        direccion=dto.address,
        activo=True,
        puesto=dto.role,
        turno=dto.shift,
    )
