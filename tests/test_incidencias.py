from __future__ import annotations

from clinicdesk.app.infrastructure.sqlite.repos_incidencias import Incidencia
from clinicdesk.app.queries.incidencias_queries import IncidenciasQueries


def test_incidencias_create_list_filter(container, seed_data, assert_expected_actual) -> None:
    incidencias_repo = container.incidencias_repo

    incidencia = Incidencia(
        tipo="CITA",
        severidad="ALTA",
        estado="ABIERTA",
        fecha_hora="2024-05-20 11:00:00",
        descripcion="Cita creada con override",
        medico_id=seed_data["medico_activo_id"],
        personal_id=seed_data["personal_activo_id"],
        cita_id=None,
        dispensacion_id=None,
        receta_id=None,
        confirmado_por_personal_id=seed_data["personal_activo_id"],
        nota_override="Aprobado por urgencia",
    )

    incidencia_id = incidencias_repo.create(incidencia)
    stored = incidencias_repo.get_by_id(incidencia_id)
    assert stored is not None

    assert_expected_actual(
        {
            "tipo": "CITA",
            "severidad": "ALTA",
            "estado": "ABIERTA",
        },
        {
            "tipo": stored.tipo,
            "severidad": stored.severidad,
            "estado": stored.estado,
        },
        message="Incidencia creada: esperado vs obtenido",
    )

    queries = IncidenciasQueries(container.connection)
    resultados = queries.list(tipo="CITA", severidad="ALTA")
    assert resultados, "Debe listar incidencias filtradas por tipo/severidad"

    assert_expected_actual(
        {
            "tipo": "CITA",
            "severidad": "ALTA",
            "confirmado_por": "Carla",
        },
        {
            "tipo": resultados[0].tipo,
            "severidad": resultados[0].severidad,
            "confirmado_por": resultados[0].confirmado_por_nombre.split(" ")[0],
        },
        message="Listado de incidencias filtrado: esperado vs obtenido",
    )

    texto = queries.list(texto="override")
    assert texto, "Filtro por texto debe encontrar incidencia creada"
