from __future__ import annotations

from clinicdesk.app.domain.modelos import Material


def test_materiales_crud_and_search(container, seed_data, assert_expected_actual) -> None:
    materiales_repo = container.materiales_repo

    material = Material(
        nombre="Mascarillas FFP2",
        fungible=True,
        cantidad_almacen=300,
        activo=True,
    )

    material_id = materiales_repo.create(material)
    stored = materiales_repo.get_by_id(material_id)
    assert stored is not None

    assert_expected_actual(
        {
            "nombre": "Mascarillas FFP2",
            "fungible": True,
            "cantidad": 300,
            "activo": True,
        },
        {
            "nombre": stored.nombre,
            "fungible": stored.fungible,
            "cantidad": stored.cantidad_en_almacen,
            "activo": stored.activo,
        },
        message="Material creado: esperado vs obtenido",
    )

    stored.cantidad_en_almacen = 280
    stored.nombre = "Mascarillas FFP2 Azul"
    materiales_repo.update(stored)

    updated = materiales_repo.get_by_id(material_id)
    assert updated is not None

    assert_expected_actual(
        {
            "nombre": "Mascarillas FFP2 Azul",
            "cantidad": 280,
        },
        {
            "nombre": updated.nombre,
            "cantidad": updated.cantidad_en_almacen,
        },
        message="Material actualizado: esperado vs obtenido",
    )

    materiales_repo.delete(material_id)
    activos = materiales_repo.list_all(solo_activos=True)
    assert all(m.id != material_id for m in activos), "Material desactivado no debe estar activo"

    encontrados = materiales_repo.search(texto="Guantes")
    nombres = [m.nombre for m in encontrados]
    assert "Guantes nitrilo" in nombres, "Búsqueda parcial debe encontrar material activo"

    inactivos = materiales_repo.search(activo=False)
    inactivos_ids = [m.id for m in inactivos]
    assert seed_data["material_inactivo_id"] in inactivos_ids, "Material inactivo debe aparecer en activo=False"
