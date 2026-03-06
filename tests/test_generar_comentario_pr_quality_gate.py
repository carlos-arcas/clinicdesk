from __future__ import annotations

from pathlib import Path

from scripts.ci import generar_comentario_pr_quality_gate as modulo


def test_genera_markdown_con_marcador(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)
    (tmp_path / "quality_report.md").write_text("linea 1\nlinea 2\n", encoding="utf-8")

    salida = modulo.generar_markdown("success", "https://github.com/run/1")

    assert salida.startswith(modulo.MARCADOR_COMENTARIO)
    assert "**Outcome:** `success`" in salida
    assert "https://github.com/run/1" in salida
    assert "**Ruff format diff artifact:** `no generado`" in salida


def test_indica_diff_ruff_disponible(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)
    (tmp_path / "ruff_format_diff.txt").write_text("diff", encoding="utf-8")

    salida = modulo.generar_markdown("failure", "https://run")

    assert "**Ruff format diff artifact:** `disponible`" in salida
    assert "BEGIN/END RUFF FORMAT DIFF" in salida
    assert "docs/ruff_format_diff.txt" in salida


def test_indica_diff_ruff_no_generado_con_mensaje_sobrio(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)

    salida = modulo.generar_markdown("failure", "https://run")

    assert "**Ruff format diff artifact:** `no generado`" in salida
    assert "Sin diff Ruff generado." in salida


def test_recorta_head_y_tail(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)
    lineas = [f"linea {i}" for i in range(1, 101)]
    (tmp_path / "quality_report.md").write_text("\n".join(lineas), encoding="utf-8")
    (tmp_path / "pip_audit_report.txt").write_text("\n".join(lineas), encoding="utf-8")

    salida = modulo.generar_markdown("failure", "https://run")

    assert "linea 1" in salida
    assert "linea 40" in salida
    assert "linea 41" not in salida
    assert "linea 61" in salida
    assert "linea 60" not in salida


def test_redaccion_basica_enmascara_datos_sensibles() -> None:
    texto = "mail ana@example.com tel +34 600 123 123 dni 12345678Z token sk_ABCDEFGH1234"

    redactado = modulo.redactar_texto(texto)

    assert "example.com" not in redactado
    assert "12345678Z" not in redactado
    assert "sk_ABCDEFGH1234" not in redactado
    assert redactado.count("[REDACTED]") >= 4


def test_no_falla_si_faltan_ficheros(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)

    salida = modulo.generar_markdown("unknown", "")

    assert "(no encontrado)" in salida
    assert "`no disponible`" in salida


def test_cobertura_desde_xml(tmp_path: Path, monkeypatch) -> None:
    _apuntar_rutas_tmp(tmp_path, monkeypatch)
    (tmp_path / "coverage.xml").write_text('<coverage line-rate="0.873"/>', encoding="utf-8")

    cobertura = modulo.obtener_cobertura()

    assert cobertura == "87.30%"


def _apuntar_rutas_tmp(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(modulo, "RUTA_REPORTE_CALIDAD", tmp_path / "quality_report.md")
    monkeypatch.setattr(modulo, "RUTA_COBERTURA_JSON", tmp_path / "coverage.json")
    monkeypatch.setattr(modulo, "RUTA_COBERTURA_XML", tmp_path / "coverage.xml")
    monkeypatch.setattr(modulo, "RUTA_PIP_AUDIT", tmp_path / "pip_audit_report.txt")
    monkeypatch.setattr(modulo, "RUTA_SECRETS", tmp_path / "secrets_scan_report.txt")
    monkeypatch.setattr(modulo, "RUTA_RUFF_FORMAT_DIFF", tmp_path / "ruff_format_diff.txt")
