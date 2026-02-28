from __future__ import annotations

import random
import sqlite3
from datetime import date, datetime, timedelta


def seed_inventory(connection: sqlite3.Connection, n_meds: int, n_materials: int) -> tuple[int, int]:
    meds = max(1, n_meds)
    materials = max(1, n_materials)
    for idx in range(meds):
        connection.execute(
            """INSERT INTO medicamentos (nombre_compuesto, nombre_comercial, cantidad_en_almacen, activo)
            VALUES (?, ?, ?, 1)""",
            (f"Compuesto {idx:03d}", f"Medicamento {idx:03d}", 20 + (idx % 200)),
        )
    for idx in range(materials):
        connection.execute(
            """INSERT INTO materiales (nombre, fungible, cantidad_en_almacen, activo)
            VALUES (?, ?, ?, 1)""",
            (f"Material {idx:03d}", 1 if idx % 3 else 0, 10 + (idx % 120)),
        )
    connection.commit()
    return meds, materials


def seed_recetas_dispensaciones(
    connection: sqlite3.Connection,
    patient_ids: list[int],
    doctor_ids: list[int],
    staff_ids: list[int],
    n_recetas: int,
    seed: int,
    from_date: date,
    to_date: date,
) -> tuple[int, int, int]:
    med_ids = [r[0] for r in connection.execute("SELECT id FROM medicamentos WHERE activo = 1").fetchall()]
    if not med_ids:
        return 0, 0, 0
    rng = random.Random(seed + 7000)
    recipes = max(1, n_recetas)
    total_lineas = 0
    total_disp = 0
    for idx in range(recipes):
        d = from_date + timedelta(days=rng.randint(0, max((to_date - from_date).days, 1)))
        receta_cur = connection.execute(
            """INSERT INTO recetas (paciente_id, medico_id, fecha, observaciones, estado, activo)
            VALUES (?, ?, ?, ?, 'ACTIVA', 1)""",
            (patient_ids[idx % len(patient_ids)], doctor_ids[idx % len(doctor_ids)], f"{d.isoformat()} 10:00:00", "Receta demo"),
        )
        receta_id = int(receta_cur.lastrowid)
        for line_idx in range(rng.randint(1, 5)):
            cantidad = rng.randint(1, 4)
            pendiente = rng.randint(0, cantidad)
            linea_cur = connection.execute(
                """INSERT INTO receta_lineas (receta_id, medicamento_id, dosis, duracion_dias, instrucciones,
                cantidad, pendiente, estado, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
                (receta_id, med_ids[(idx + line_idx) % len(med_ids)], "1 cada 8h", 7 + line_idx, "Tras comida", cantidad, pendiente, "PENDIENTE" if pendiente else "DISPENSADA"),
            )
            total_lineas += 1
            if staff_ids:
                disp_fecha = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 20))
                connection.execute(
                    """INSERT INTO dispensaciones (receta_id, receta_linea_id, medicamento_id, personal_id, fecha_hora,
                    cantidad, observaciones, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                    (receta_id, int(linea_cur.lastrowid), med_ids[(idx + line_idx) % len(med_ids)], staff_ids[(idx + line_idx) % len(staff_ids)], disp_fecha.isoformat(sep=" ", timespec="seconds"), max(1, cantidad - pendiente), "Dispensación demo"),
                )
                total_disp += 1
    connection.commit()
    return recipes, total_lineas, total_disp


def seed_movimientos(connection: sqlite3.Connection, n_movimientos: int, staff_ids: list[int], seed: int, has_recetas: bool) -> tuple[int, int]:
    rng = random.Random(seed + 8000)
    med_ids = [r[0] for r in connection.execute("SELECT id FROM medicamentos WHERE activo = 1").fetchall()]
    mat_ids = [r[0] for r in connection.execute("SELECT id FROM materiales WHERE activo = 1").fetchall()]
    total_med = max(1, n_movimientos // 2)
    total_mat = max(1, n_movimientos - total_med)
    for idx in range(total_med):
        ts = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 40))
        connection.execute(
            """INSERT INTO movimientos_medicamentos (medicamento_id, fecha_hora, tipo, cantidad, motivo, personal_id, referencia, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (med_ids[idx % len(med_ids)], ts.isoformat(sep=" ", timespec="seconds"), "ENTRADA" if idx % 5 else "SALIDA", rng.randint(1, 20), "Movimiento demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, "seed-demo" if has_recetas else "seed"),
        )
    for idx in range(total_mat):
        ts = datetime.now().replace(microsecond=0) - timedelta(days=rng.randint(0, 40))
        connection.execute(
            """INSERT INTO movimientos_materiales (material_id, fecha_hora, tipo, cantidad, motivo, personal_id, referencia, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (mat_ids[idx % len(mat_ids)], ts.isoformat(sep=" ", timespec="seconds"), "ENTRADA" if idx % 4 else "SALIDA", rng.randint(1, 15), "Movimiento demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, "seed-demo"),
        )
    connection.commit()
    return total_med, total_mat


def seed_turnos_y_calendario(connection: sqlite3.Connection, doctor_ids: list[int], staff_ids: list[int], months: int) -> int:
    defaults = [("Mañana", "08:00", "14:00"), ("Tarde", "14:00", "20:00")]
    turnos_ids: list[int] = []
    for nombre, ini, fin in defaults:
        cur = connection.execute("INSERT OR IGNORE INTO turnos (nombre, hora_inicio, hora_fin, activo) VALUES (?, ?, ?, 1)", (nombre, ini, fin))
        if cur.lastrowid:
            turnos_ids.append(int(cur.lastrowid))
    if not turnos_ids:
        turnos_ids = [r[0] for r in connection.execute("SELECT id FROM turnos WHERE activo = 1").fetchall()]
    start = date.today().replace(day=1)
    days = max(30, months * 30)
    for offset in range(days):
        d = start + timedelta(days=offset)
        for mid in doctor_ids:
            connection.execute("INSERT OR IGNORE INTO calendario_medico (medico_id, fecha, turno_id, activo) VALUES (?, ?, ?, 1)", (mid, d.isoformat(), turnos_ids[(mid + offset) % len(turnos_ids)]))
        for pid in staff_ids:
            connection.execute("INSERT OR IGNORE INTO calendario_personal (personal_id, fecha, turno_id, activo) VALUES (?, ?, ?, 1)", (pid, d.isoformat(), turnos_ids[(pid + offset) % len(turnos_ids)]))
    connection.commit()
    return len(turnos_ids)


def seed_ausencias(connection: sqlite3.Connection, doctor_ids: list[int], staff_ids: list[int], total: int, seed: int) -> int:
    rng = random.Random(seed + 9000)
    tipos = ["VACACIONES", "BAJA", "DIA_SUELTO"]
    created = 0
    for idx in range(max(1, total // 2)):
        ini = datetime.now().date() + timedelta(days=rng.randint(-20, 20))
        fin = ini + timedelta(days=rng.randint(0, 5))
        connection.execute(
            "INSERT INTO ausencias_medico (medico_id, inicio, fin, tipo, motivo, aprobado_por_personal_id, creado_en, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (doctor_ids[idx % len(doctor_ids)], ini.isoformat(), fin.isoformat(), tipos[idx % len(tipos)], "Ausencia demo", staff_ids[idx % len(staff_ids)] if staff_ids else None, datetime.now().isoformat(sep=" ", timespec="seconds")),
        )
        created += 1
    for idx in range(max(1, total - created)):
        ini = datetime.now().date() + timedelta(days=rng.randint(-20, 20))
        fin = ini + timedelta(days=rng.randint(0, 3))
        connection.execute(
            "INSERT INTO ausencias_personal (personal_id, inicio, fin, tipo, motivo, aprobado_por_personal_id, creado_en, activo) VALUES (?, ?, ?, ?, ?, ?, ?, 1)",
            (staff_ids[idx % len(staff_ids)], ini.isoformat(), fin.isoformat(), tipos[(idx + 1) % len(tipos)], "Ausencia demo", staff_ids[(idx + 1) % len(staff_ids)] if staff_ids else None, datetime.now().isoformat(sep=" ", timespec="seconds")),
        )
        created += 1
    connection.commit()
    return created
