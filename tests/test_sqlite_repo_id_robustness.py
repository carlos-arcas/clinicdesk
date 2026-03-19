from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from clinicdesk.app.domain.enums import EstadoCita, TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Cita, Material, Medicamento, Medico, Personal, Receta, RecetaLinea, Sala
from clinicdesk.app.infrastructure.sqlite.id_utils import SqliteIntegrityError, require_entero_sqlite
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_medico import AusenciaMedico
from clinicdesk.app.infrastructure.sqlite.repos_ausencias_personal import AusenciaPersonal
from clinicdesk.app.infrastructure.sqlite.repos_calendario_medico import BloqueCalendarioMedico
from clinicdesk.app.infrastructure.sqlite.repos_calendario_personal import BloqueCalendarioPersonal
from clinicdesk.app.infrastructure.sqlite.repos_dispensaciones import Dispensacion
from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia
from clinicdesk.app.infrastructure.sqlite.repos_movimientos_materiales import MovimientoMaterial
from clinicdesk.app.infrastructure.sqlite.repos_movimientos_medicamentos import MovimientoMedicamento
from clinicdesk.app.infrastructure.sqlite.repos_turnos import Turno


def test_require_entero_sqlite_rechaza_none() -> None:
    with pytest.raises(SqliteIntegrityError, match="entero SQLite válido"):
        require_entero_sqlite(None, context="test")


def test_repos_soft_delete_excluye_getters_directos(container) -> None:
    personal = Personal(
        tipo_documento=TipoDocumento.DNI,
        documento="44556677",
        nombre="Nora",
        apellidos="Gil",
        telefono=None,
        email=None,
        fecha_nacimiento=None,
        direccion=None,
        activo=True,
        puesto="Recepcion",
        turno=None,
    )
    personal_id = container.personal_repo.create(personal)
    container.personal_repo.delete(personal_id)
    assert container.personal_repo.get_by_id(personal_id) is None
    assert container.personal_repo.get_id_by_documento(TipoDocumento.DNI, "44556677") is None
    assert container.personal_repo.get_id_by_nombre("Nora", "Gil") is None

    medico_id = container.medicos_repo.create(
        Medico(
            tipo_documento=TipoDocumento.DNI,
            documento="55443322",
            nombre="Mario",
            apellidos="Sanz",
            telefono=None,
            email=None,
            fecha_nacimiento=None,
            direccion=None,
            activo=True,
            num_colegiado="MED-990",
            especialidad="Urgencias",
        )
    )
    container.medicos_repo.delete(medico_id)
    assert container.medicos_repo.get_by_id(medico_id) is None
    assert container.medicos_repo.get_id_by_documento(TipoDocumento.DNI, "55443322") is None

    medicamento_id = container.medicamentos_repo.create(
        Medicamento(
            nombre_compuesto="Metamizol",
            nombre_comercial="Nolotil",
            cantidad_almacen=10,
            activo=True,
        )
    )
    container.medicamentos_repo.delete(medicamento_id)
    assert container.medicamentos_repo.get_by_id(medicamento_id) is None
    assert container.medicamentos_repo.get_id_by_nombre("Nolotil") is None

    material_id = container.materiales_repo.create(
        Material(nombre="Jeringa 5ml", fungible=True, cantidad_almacen=40, activo=True)
    )
    container.materiales_repo.delete(material_id)
    assert container.materiales_repo.get_by_id(material_id) is None

    sala_id = container.salas_repo.create(
        Sala(nombre="Box 9", tipo=TipoSala.CONSULTA, ubicacion="Planta 1", activa=True)
    )
    container.salas_repo.delete(sala_id)
    assert container.salas_repo.get_by_id(sala_id) is None


def test_repo_recetas_getter_directo_y_lineas_respetan_soft_delete(container, seed_data) -> None:
    receta_id = container.recetas_repo.create_receta(
        Receta(
            paciente_id=seed_data["paciente_activo_id"],
            medico_id=seed_data["medico_activo_id"],
            fecha=datetime(2026, 1, 15, 9, 0, 0),
            observaciones="Control temporal",
        )
    )
    linea_id = container.recetas_repo.add_linea(
        RecetaLinea(
            receta_id=receta_id,
            medicamento_id=seed_data["medicamento_activo_id"],
            dosis="1 diaria",
            duracion_dias=3,
            instrucciones=None,
        )
    )

    assert container.recetas_repo.get_receta_by_id(receta_id) is not None
    assert [linea.id for linea in container.recetas_repo.list_lineas_by_receta(receta_id)] == [linea_id]

    container.recetas_repo.delete_linea(linea_id)
    assert container.recetas_repo.list_lineas_by_receta(receta_id) == []

    container.recetas_repo.delete_receta(receta_id)
    assert container.recetas_repo.get_receta_by_id(receta_id) is None


def test_repos_sqlite_soft_delete_round2_coherencia_contrato(container, seed_data) -> None:
    turno_id = container.turnos_repo.create(
        Turno(nombre="Turno tarde", hora_inicio="15:00", hora_fin="21:00", activo=True)
    )
    assert isinstance(turno_id, int) and turno_id > 0
    assert container.turnos_repo.get_by_id(turno_id) is not None
    assert [turno.id for turno in container.turnos_repo.search(nombre="tarde")] == [turno_id]
    container.turnos_repo.delete(turno_id)
    assert container.turnos_repo.get_by_id(turno_id) is None
    assert container.turnos_repo.search(nombre="tarde") == []

    bloque_medico_id = container.calendario_medico_repo.create(
        BloqueCalendarioMedico(
            medico_id=seed_data["medico_activo_id"],
            fecha="2024-05-21",
            turno_id=seed_data["turno_id"],
            observaciones="Cobertura tarde",
        )
    )
    assert isinstance(bloque_medico_id, int) and bloque_medico_id > 0
    assert container.calendario_medico_repo.get_by_id(bloque_medico_id) is not None
    assert [bloque.id for bloque in container.calendario_medico_repo.list_by_medico(seed_data["medico_activo_id"])] == [
        1,
        bloque_medico_id,
    ]
    container.calendario_medico_repo.delete(bloque_medico_id)
    assert container.calendario_medico_repo.get_by_id(bloque_medico_id) is None
    assert [bloque.id for bloque in container.calendario_medico_repo.list_by_medico(seed_data["medico_activo_id"])] == [
        1
    ]

    bloque_personal_id = container.calendario_personal_repo.create(
        BloqueCalendarioPersonal(
            personal_id=seed_data["personal_activo_id"],
            fecha="2024-05-21",
            turno_id=seed_data["turno_id"],
            observaciones="Refuerzo mañana",
        )
    )
    assert isinstance(bloque_personal_id, int) and bloque_personal_id > 0
    assert container.calendario_personal_repo.get_by_id(bloque_personal_id) is not None
    assert [
        bloque.id for bloque in container.calendario_personal_repo.list_by_personal(seed_data["personal_activo_id"])
    ] == [bloque_personal_id]
    container.calendario_personal_repo.delete(bloque_personal_id)
    assert container.calendario_personal_repo.get_by_id(bloque_personal_id) is None
    assert container.calendario_personal_repo.list_by_personal(seed_data["personal_activo_id"]) == []

    cita_id = container.citas_repo.create(
        Cita(
            paciente_id=seed_data["paciente_activo_id"],
            medico_id=seed_data["medico_activo_id"],
            sala_id=seed_data["sala_activa_id"],
            inicio=datetime(2024, 5, 23, 9, 0, 0),
            fin=datetime(2024, 5, 23, 9, 30, 0),
            motivo="Revisión round2",
            notas="Sin incidencias",
            estado=EstadoCita.PROGRAMADA,
        )
    )
    assert isinstance(cita_id, int) and cita_id > 0
    assert container.citas_repo.get_by_id(cita_id) is not None
    assert [cita.id for cita in container.citas_repo.list_by_medico(seed_data["medico_activo_id"])] == [cita_id]
    container.citas_repo.delete(cita_id)
    assert container.citas_repo.get_by_id(cita_id) is None
    assert container.citas_repo.list_by_medico(seed_data["medico_activo_id"]) == []

    movimiento_material_id = container.mov_materiales_repo.create(
        MovimientoMaterial(
            material_id=seed_data["material_activo_id"],
            tipo="ENTRADA",
            cantidad=5,
            fecha_hora="2024-05-20 08:00:00",
            personal_id=seed_data["personal_activo_id"],
            motivo="Reposición",
            referencia="ALB-01",
        )
    )
    assert isinstance(movimiento_material_id, int) and movimiento_material_id > 0
    assert container.mov_materiales_repo.get_by_id(movimiento_material_id) is not None
    assert [mov.id for mov in container.mov_materiales_repo.list_by_material(seed_data["material_activo_id"])] == [
        movimiento_material_id
    ]
    container.mov_materiales_repo.delete(movimiento_material_id)
    assert container.mov_materiales_repo.get_by_id(movimiento_material_id) is None
    assert container.mov_materiales_repo.list_by_material(seed_data["material_activo_id"]) == []

    movimiento_medicamento_id = container.mov_medicamentos_repo.create(
        MovimientoMedicamento(
            medicamento_id=seed_data["medicamento_activo_id"],
            tipo="SALIDA",
            cantidad=-2,
            fecha_hora="2024-05-20 08:05:00",
            personal_id=seed_data["personal_activo_id"],
            motivo="Dispensación",
            referencia="REC-01",
        )
    )
    assert isinstance(movimiento_medicamento_id, int) and movimiento_medicamento_id > 0
    assert container.mov_medicamentos_repo.get_by_id(movimiento_medicamento_id) is not None
    assert [
        mov.id for mov in container.mov_medicamentos_repo.list_by_medicamento(seed_data["medicamento_activo_id"])
    ] == [movimiento_medicamento_id]
    container.mov_medicamentos_repo.delete(movimiento_medicamento_id)
    assert container.mov_medicamentos_repo.get_by_id(movimiento_medicamento_id) is None
    assert container.mov_medicamentos_repo.list_by_medicamento(seed_data["medicamento_activo_id"]) == []

    dispensacion_id = container.dispensaciones_repo.create(
        Dispensacion(
            receta_id=seed_data["receta_id"],
            receta_linea_id=seed_data["receta_linea_id"],
            medicamento_id=seed_data["medicamento_activo_id"],
            personal_id=seed_data["personal_activo_id"],
            cantidad=1,
            fecha_hora="2024-05-20 10:30:00",
            incidencia=False,
            notas_incidencia=None,
        )
    )
    assert isinstance(dispensacion_id, int) and dispensacion_id > 0
    assert container.dispensaciones_repo.get_by_id(dispensacion_id) is not None
    assert [disp.id for disp in container.dispensaciones_repo.list_by_receta(seed_data["receta_id"])] == [
        dispensacion_id
    ]
    container.dispensaciones_repo.delete(dispensacion_id)
    assert container.dispensaciones_repo.get_by_id(dispensacion_id) is None
    assert container.dispensaciones_repo.list_by_receta(seed_data["receta_id"]) == []

    ausencia_medico_id = container.ausencias_medico_repo.create(
        AusenciaMedico(
            medico_id=seed_data["medico_activo_id"],
            inicio="2024-05-25 08:00:00",
            fin="2024-05-25 14:00:00",
            tipo="VACACIONES",
            motivo="Descanso",
            aprobado_por_personal_id=seed_data["personal_activo_id"],
            creado_en="2024-05-20 08:00:00",
        )
    )
    assert isinstance(ausencia_medico_id, int) and ausencia_medico_id > 0
    assert container.ausencias_medico_repo.get_by_id(ausencia_medico_id) is not None
    assert [aus.id for aus in container.ausencias_medico_repo.list_by_medico(seed_data["medico_activo_id"])] == [
        ausencia_medico_id
    ]
    container.ausencias_medico_repo.delete(ausencia_medico_id)
    assert container.ausencias_medico_repo.get_by_id(ausencia_medico_id) is None
    assert container.ausencias_medico_repo.list_by_medico(seed_data["medico_activo_id"]) == []

    ausencia_personal_id = container.ausencias_personal_repo.create(
        AusenciaPersonal(
            personal_id=seed_data["personal_activo_id"],
            inicio="2024-05-26 08:00:00",
            fin="2024-05-26 14:00:00",
            tipo="PERMISO",
            motivo="Gestión",
            aprobado_por_personal_id=seed_data["personal_activo_id"],
            creado_en="2024-05-20 08:00:00",
        )
    )
    assert isinstance(ausencia_personal_id, int) and ausencia_personal_id > 0
    assert container.ausencias_personal_repo.get_by_id(ausencia_personal_id) is not None
    assert [aus.id for aus in container.ausencias_personal_repo.list_by_personal(seed_data["personal_activo_id"])] == [
        ausencia_personal_id
    ]
    container.ausencias_personal_repo.delete(ausencia_personal_id)
    assert container.ausencias_personal_repo.get_by_id(ausencia_personal_id) is None
    assert container.ausencias_personal_repo.list_by_personal(seed_data["personal_activo_id"]) == []

    incidencia_id = container.incidencias_repo.create(
        Incidencia(
            tipo="CITA",
            severidad="MEDIA",
            estado="ABIERTA",
            fecha_hora="2024-05-20 11:00:00",
            descripcion="Warning controlado",
            medico_id=seed_data["medico_activo_id"],
            personal_id=seed_data["personal_activo_id"],
            cita_id=None,
            dispensacion_id=None,
            receta_id=seed_data["receta_id"],
            confirmado_por_personal_id=seed_data["personal_activo_id"],
            nota_override="Se registra para auditoría",
        )
    )
    assert isinstance(incidencia_id, int) and incidencia_id > 0
    assert container.incidencias_repo.get_by_id(incidencia_id) is not None
    assert [inc.id for inc in container.incidencias_repo.search(receta_id=seed_data["receta_id"])] == [incidencia_id]
    container.incidencias_repo.delete(incidencia_id)
    assert container.incidencias_repo.get_by_id(incidencia_id) is None
    assert container.incidencias_repo.search(receta_id=seed_data["receta_id"]) == []


def test_repos_objetivo_no_reintroducen_lastrowid_directo() -> None:
    rutas = [
        "clinicdesk/app/infrastructure/sqlite/repos_turnos.py",
        "clinicdesk/app/infrastructure/sqlite/repos_citas.py",
        "clinicdesk/app/infrastructure/sqlite/repos_dispensaciones.py",
        "clinicdesk/app/infrastructure/sqlite/repos_calendario_medico.py",
        "clinicdesk/app/infrastructure/sqlite/repos_calendario_personal.py",
        "clinicdesk/app/infrastructure/sqlite/repos_movimientos_materiales.py",
        "clinicdesk/app/infrastructure/sqlite/repos_movimientos_medicamentos.py",
        "clinicdesk/app/infrastructure/sqlite/repos_ausencias_medico.py",
        "clinicdesk/app/infrastructure/sqlite/repos_ausencias_personal.py",
        "clinicdesk/app/infrastructure/sqlite/repos_incidencias.py",
        "clinicdesk/app/infrastructure/sqlite/repos_pacientes.py",
    ]
    for ruta in rutas:
        contenido = Path(ruta).read_text(encoding="utf-8")
        assert "int(cur.lastrowid)" not in contenido, ruta
