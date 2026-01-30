from __future__ import annotations

from clinicdesk.app.domain.enums import TipoSala
from clinicdesk.app.domain.modelos import Sala


def test_salas_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    salas_repo = container.salas_repo

    sala = Sala(
        nombre="Consulta 2",
        tipo=TipoSala.CONSULTA,
        ubicacion="Planta 2",
        activa=True,
    )

    sala_id = salas_repo.create(sala)
    stored = salas_repo.get_by_id(sala_id)
    assert stored is not None

    assert_expected_actual(
        {
            "nombre": "Consulta 2",
            "tipo": TipoSala.CONSULTA,
            "ubicacion": "Planta 2",
            "activa": True,
        },
        {
            "nombre": stored.nombre,
            "tipo": stored.tipo,
            "ubicacion": stored.ubicacion,
            "activa": stored.activa,
        },
        message="Sala creada: esperado vs obtenido",
    )

    stored.ubicacion = "Planta 3"
    stored.tipo = TipoSala.OTRO
    salas_repo.update(stored)

    updated = salas_repo.get_by_id(sala_id)
    assert updated is not None

    assert_expected_actual(
        {
            "tipo": TipoSala.OTRO,
            "ubicacion": "Planta 3",
        },
        {
            "tipo": updated.tipo,
            "ubicacion": updated.ubicacion,
        },
        message="Sala actualizada: esperado vs obtenido",
    )

    salas_repo.delete(sala_id)
    activas = salas_repo.list_all(solo_activas=True)
    assert all(s.id != sala_id for s in activas), "Sala desactivada no debe estar activa"

    encontrados = salas_repo.search(texto="Consulta")
    nombres = [s.nombre for s in encontrados]
    assert "Consulta 1" in nombres, "Búsqueda parcial debe encontrar salas activas"

    inactivas = salas_repo.search(activa=False)
    inactivas_ids = [s.id for s in inactivas]
    assert seed_data["sala_inactiva_id"] in inactivas_ids, "Sala inactiva debe aparecer en activa=False"
