from __future__ import annotations

from datetime import datetime

import pytest

from clinicdesk.app.domain.enums import TipoDocumento, TipoSala
from clinicdesk.app.domain.modelos import Material, Medicamento, Medico, Personal, Receta, RecetaLinea, Sala
from clinicdesk.app.infrastructure.sqlite.id_utils import SqliteIntegrityError, require_entero_sqlite


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
