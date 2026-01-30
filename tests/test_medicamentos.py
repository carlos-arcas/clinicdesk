from __future__ import annotations

from clinicdesk.app.domain.modelos import Medicamento


def test_medicamentos_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    medicamentos_repo = container.medicamentos_repo

    medicamento = Medicamento(
        nombre_compuesto="Paracetamol",
        nombre_comercial="Gelocatil",
        cantidad_almacen=50,
        activo=True,
    )

    medicamento_id = medicamentos_repo.create(medicamento)
    stored = medicamentos_repo.get_by_id(medicamento_id)
    assert stored is not None

    assert_expected_actual(
        {
            "nombre_compuesto": "Paracetamol",
            "nombre_comercial": "Gelocatil",
            "cantidad": 50,
            "activo": True,
        },
        {
            "nombre_compuesto": stored.nombre_compuesto,
            "nombre_comercial": stored.nombre_comercial,
            "cantidad": stored.cantidad_en_almacen,
            "activo": stored.activo,
        },
        message="Medicamento creado: esperado vs obtenido",
    )

    stored.cantidad_en_almacen = 25
    stored.nombre_comercial = "Gelocatil Forte"
    medicamentos_repo.update(stored)

    updated = medicamentos_repo.get_by_id(medicamento_id)
    assert updated is not None

    assert_expected_actual(
        {
            "nombre_comercial": "Gelocatil Forte",
            "cantidad": 25,
        },
        {
            "nombre_comercial": updated.nombre_comercial,
            "cantidad": updated.cantidad_en_almacen,
        },
        message="Medicamento actualizado: esperado vs obtenido",
    )

    medicamentos_repo.delete(medicamento_id)
    activos = medicamentos_repo.list_all(solo_activos=True)
    assert all(m.id != medicamento_id for m in activos), "Medicamento desactivado no debe estar activo"

    encontrados = medicamentos_repo.search(texto="Amox")
    nombres = [m.nombre_comercial for m in encontrados]
    assert "Amoxil" in nombres, "Búsqueda parcial por nombre debe encontrar medicamento activo"

    inactivos = medicamentos_repo.search(activo=False)
    inactivos_ids = [m.id for m in inactivos]
    assert seed_data["medicamento_inactivo_id"] in inactivos_ids, "Medicamento inactivo debe aparecer en activo=False"
