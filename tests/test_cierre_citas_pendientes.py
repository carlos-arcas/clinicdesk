from __future__ import annotations

from datetime import datetime, timedelta

from clinicdesk.app.application.prediccion_ausencias.cierre_citas_usecases import (
    CierreCitaItemRequest,
    CerrarCitasPendientes,
    CerrarCitasPendientesRequest,
    ListarCitasPendientesCierre,
    PaginacionPendientesCierre,
)
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries


def _seed_base_tablas(con) -> tuple[int, int, int, int]:
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '1', 'Ana', 'Uno', 1)"
    )
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '2', 'Beto', 'Dos', 1)"
    )
    con.execute(
        "INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, activo, num_colegiado, especialidad) VALUES ('DNI', '11', 'Med', 'Uno', 1, 'C1', 'General')"
    )
    con.execute("INSERT INTO salas(nombre, tipo, activa) VALUES ('S1', 'CONSULTA', 1)")
    con.commit()
    return 1, 2, 1, 1


def _insert_cita(con, *, paciente_id: int, medico_id: int, sala_id: int, inicio: datetime, estado: str) -> int:
    fin = inicio + timedelta(minutes=30)
    cur = con.execute(
        """
        INSERT INTO citas(paciente_id, medico_id, sala_id, inicio, fin, estado, activo)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (paciente_id, medico_id, sala_id, inicio.isoformat(), fin.isoformat(), estado),
    )
    return int(cur.lastrowid)


def test_listar_citas_pendientes_cierre_filtra_pasadas_no_finales_y_pagina(db_connection) -> None:
    paciente_1, paciente_2, medico_id, sala_id = _seed_base_tablas(db_connection)
    ahora = datetime.now()
    _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=8), estado="PROGRAMADA")
    _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=6), estado="CONFIRMADA")
    _insert_cita(db_connection, paciente_id=paciente_2, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=5), estado="EN_CURSO")
    _insert_cita(db_connection, paciente_id=paciente_2, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=4), estado="REALIZADA")
    _insert_cita(db_connection, paciente_id=paciente_2, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=3), estado="NO_PRESENTADO")
    _insert_cita(db_connection, paciente_id=paciente_2, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=2), estado="CANCELADA")
    _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora + timedelta(days=2), estado="PROGRAMADA")
    db_connection.commit()

    queries = PrediccionAusenciasQueries(db_connection)
    uc = ListarCitasPendientesCierre(queries)
    primera_pagina = uc.ejecutar(PaginacionPendientesCierre(limite=2, offset=0))
    segunda_pagina = uc.ejecutar(PaginacionPendientesCierre(limite=2, offset=2))

    assert primera_pagina.total == 3
    assert len(primera_pagina.items) == 2
    assert primera_pagina.items[0].estado_actual == "PROGRAMADA"
    assert primera_pagina.items[1].estado_actual == "CONFIRMADA"
    assert len(segunda_pagina.items) == 1
    assert segunda_pagina.items[0].estado_actual == "EN_CURSO"


def test_cerrar_citas_en_lote_actualiza_e_ignora_dejar_igual(db_connection) -> None:
    paciente_1, _, medico_id, sala_id = _seed_base_tablas(db_connection)
    ahora = datetime.now()
    cita_1 = _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=10), estado="PROGRAMADA")
    cita_2 = _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=9), estado="CONFIRMADA")
    cita_3 = _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=8), estado="EN_CURSO")
    db_connection.commit()

    queries = PrediccionAusenciasQueries(db_connection)
    uc = CerrarCitasPendientes(queries)
    request = CerrarCitasPendientesRequest(
        items=[
            CierreCitaItemRequest(cita_id=cita_1, nuevo_estado="REALIZADA"),
            CierreCitaItemRequest(cita_id=cita_2, nuevo_estado="NO_PRESENTADO"),
            CierreCitaItemRequest(cita_id=cita_3, nuevo_estado="DEJAR_IGUAL"),
        ]
    )

    resultado = uc.ejecutar(request)
    estados = {
        row["id"]: row["estado"]
        for row in db_connection.execute("SELECT id, estado FROM citas WHERE id IN (?, ?, ?)", (cita_1, cita_2, cita_3)).fetchall()
    }

    assert resultado.actualizadas == 2
    assert resultado.ignoradas == 1
    assert estados[cita_1] == "REALIZADA"
    assert estados[cita_2] == "NO_PRESENTADO"
    assert estados[cita_3] == "EN_CURSO"


def test_cerrar_citas_aumenta_citas_validas_recientes_en_ventana(db_connection) -> None:
    paciente_1, _, medico_id, sala_id = _seed_base_tablas(db_connection)
    ahora = datetime.now()
    cita_1 = _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=3), estado="PROGRAMADA")
    cita_2 = _insert_cita(db_connection, paciente_id=paciente_1, medico_id=medico_id, sala_id=sala_id, inicio=ahora - timedelta(days=2), estado="CONFIRMADA")
    db_connection.commit()

    queries = PrediccionAusenciasQueries(db_connection)
    total_antes = queries.contar_citas_validas_recientes(dias=90)

    uc = CerrarCitasPendientes(queries)
    uc.ejecutar(
        CerrarCitasPendientesRequest(
            items=[
                CierreCitaItemRequest(cita_id=cita_1, nuevo_estado="REALIZADA"),
                CierreCitaItemRequest(cita_id=cita_2, nuevo_estado="NO_PRESENTADO"),
            ]
        )
    )

    total_despues = queries.contar_citas_validas_recientes(dias=90)
    assert total_antes == 0
    assert total_despues == 2
