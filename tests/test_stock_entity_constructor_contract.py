from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6.QtWidgets import QApplication
except ImportError as exc:  # pragma: no cover - depende del entorno
    pytest.skip(f"PySide6 no disponible: {exc}", allow_module_level=True)

from clinicdesk.app.application.csv.csv_mapping import CsvMappingMixin
from clinicdesk.app.application.csv.csv_parsing import CsvParsingMixin
from clinicdesk.app.domain.modelos import Material, Medicamento
from clinicdesk.app.pages.materiales.dialogs.material_form import MaterialFormDialog
from clinicdesk.app.pages.medicamentos.dialogs.medicamento_form import MedicamentoFormDialog


class _CsvMappingStub(CsvMappingMixin, CsvParsingMixin):
    pass


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_medicamento_form_dialog_get_data_construye_entidad_valida(qapp: QApplication) -> None:
    del qapp
    dialog = MedicamentoFormDialog()
    dialog.txt_nombre_comercial.setText("Gelocatil")
    dialog.txt_nombre_compuesto.setText("Paracetamol")
    dialog.spn_stock.setValue(12)
    dialog.chk_activo.setChecked(True)

    data = dialog.get_data()

    assert data is not None
    assert data.medicamento.cantidad_almacen == 12
    assert data.medicamento.cantidad_en_almacen == 12
    dialog.close()


def test_material_form_dialog_get_data_construye_entidad_valida(qapp: QApplication) -> None:
    del qapp
    dialog = MaterialFormDialog()
    dialog.txt_nombre.setText("Gasas")
    dialog.chk_fungible.setChecked(True)
    dialog.spn_stock.setValue(7)
    dialog.chk_activo.setChecked(True)

    data = dialog.get_data()

    assert data is not None
    assert data.material.cantidad_almacen == 7
    assert data.material.cantidad_en_almacen == 7
    dialog.close()


def test_csv_mapping_medicamento_y_material_usan_cantidad_almacen_en_constructor() -> None:
    mapping = _CsvMappingStub()

    medicamento = mapping._row_to_medicamento(
        {
            "nombre_compuesto": "Ibuprofeno",
            "nombre_comercial": "Dalsy",
            "cantidad_en_almacen": "9",
            "activo": "1",
        }
    )
    material = mapping._row_to_material(
        {
            "nombre": "Jeringa",
            "fungible": "1",
            "cantidad_en_almacen": "15",
            "activo": "1",
        }
    )

    assert medicamento.cantidad_almacen == 9
    assert medicamento.cantidad_en_almacen == 9
    assert material.cantidad_almacen == 15
    assert material.cantidad_en_almacen == 15


def test_alias_cantidad_en_almacen_refleja_cantidad_almacen() -> None:
    medicamento = Medicamento(nombre_compuesto="Amoxicilina", nombre_comercial="Amoxil", cantidad_almacen=3)
    material = Material(nombre="Guantes", fungible=True, cantidad_almacen=4)

    medicamento.cantidad_en_almacen = 11
    material.cantidad_en_almacen = 13

    assert medicamento.cantidad_almacen == 11
    assert medicamento.cantidad_en_almacen == 11
    assert material.cantidad_almacen == 13
    assert material.cantidad_en_almacen == 13
