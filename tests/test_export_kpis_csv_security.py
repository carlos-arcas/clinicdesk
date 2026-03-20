from __future__ import annotations

import csv
from pathlib import Path

import pytest

from clinicdesk.app.application.usecases.export_kpis_csv import COLUMNAS_CONTRACTUALES_POR_ARCHIVO
from scripts import ml_cli
from tests.test_export_kpis_csv_e2e import _prepare_operational_pipeline

MARCADORES_SENSIBLES = {
    "cita_id",
    "paciente",
    "doctor",
    "medico",
    "sala",
    "reason",
    "reasons",
    "payload",
    "agenda",
    "Juan",
    "María",
    "Sala",
}


def test_export_kpis_csv_contract_security_only_allows_aggregated_columns_and_values(tmp_path: Path) -> None:
    outputs = _export_kpis_controlado(tmp_path)

    for nombre_archivo, columnas_esperadas in COLUMNAS_CONTRACTUALES_POR_ARCHIVO.items():
        filas = _read_csv(Path(outputs[nombre_archivo]))
        assert filas[0] == list(columnas_esperadas)
        assert set(filas[0]) == set(columnas_esperadas)
        _assert_csv_without_sensitive_content(filas)

    overview = _read_csv(Path(outputs[ml_cli.ExportKpisCSV.OVERVIEW_FILE]))
    assert all(len(fila) == len(COLUMNAS_CONTRACTUALES_POR_ARCHIVO[ml_cli.ExportKpisCSV.OVERVIEW_FILE]) for fila in overview)
    assert overview[1][5].isdigit()
    assert float(overview[1][7]) >= 0.0

    buckets = _read_csv(Path(outputs[ml_cli.ExportKpisCSV.BUCKET_FILE]))
    assert {fila[3] for fila in buckets[1:]} <= {"risk", "no_risk"}
    assert all(fila[4].isdigit() for fila in buckets[1:])

    drift = _read_csv(Path(outputs[ml_cli.ExportKpisCSV.DRIFT_FILE]))
    assert all(fila[2] for fila in drift[1:])
    assert all(fila[4] in {"GREEN", "AMBER", "RED"} for fila in drift[1:])

    training = _read_csv(Path(outputs[ml_cli.ExportKpisCSV.TRAINING_FILE]))
    assert {fila[4] for fila in training[1:]} == {"accuracy", "precision", "recall", "f1"}


def test_export_kpis_cli_returns_explicit_error_when_output_path_is_a_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rutas = _prepare_operational_pipeline(tmp_path, monkeypatch, ml_cli)
    output_file = tmp_path / "not_a_directory.csv"
    output_file.write_text("ocupado", encoding="utf-8")

    rc = ml_cli.main(
        [
            "export",
            "kpis",
            "--dataset-version",
            "ds_shifted",
            "--model-version",
            "m_shifted",
            "--predictor",
            "trained",
            "--from-version",
            "ds_base",
            "--feature-store-path",
            rutas["feature_store"],
            "--model-store-path",
            rutas["model_store"],
            "--output",
            str(output_file),
        ]
    )

    assert rc == 2
    assert output_file.read_text(encoding="utf-8") == "ocupado"


def _export_kpis_controlado(tmp_path: Path) -> dict[str, str]:
    with pytest.MonkeyPatch.context() as monkeypatch:
        rutas = _prepare_operational_pipeline(tmp_path, monkeypatch, ml_cli)
        export_dir = Path(rutas["exports_trained"])
        assert ml_cli.main(
            [
                "export",
                "kpis",
                "--dataset-version",
                "ds_shifted",
                "--model-version",
                "m_shifted",
                "--predictor",
                "trained",
                "--from-version",
                "ds_base",
                "--feature-store-path",
                rutas["feature_store"],
                "--model-store-path",
                rutas["model_store"],
                "--output",
                str(export_dir),
            ]
        ) == 0
        return {nombre: str(export_dir / nombre) for nombre in COLUMNAS_CONTRACTUALES_POR_ARCHIVO}


def _assert_csv_without_sensitive_content(filas: list[list[str]]) -> None:
    texto_plano = "\n".join(",".join(celda for celda in fila if celda is not None) for fila in filas)
    texto_normalizado = texto_plano.casefold()
    for marcador in MARCADORES_SENSIBLES:
        assert marcador.casefold() not in texto_normalizado


def _read_csv(path: Path) -> list[list[str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))
