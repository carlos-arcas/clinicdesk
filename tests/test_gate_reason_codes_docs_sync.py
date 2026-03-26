from __future__ import annotations

import textwrap

from scripts import gate_pr
from scripts.quality_gate_components.contrato_reason_codes_doc import (
    ErrorContratoReasonCodesDoc,
    comparar_reason_codes,
    extraer_snippets_semantica_bloqueo_operativo,
    extraer_reason_codes_documentados,
)


def _render_doc_glosario(
    filas: tuple[str, ...],
    *,
    titulo: str = "## Glosario breve de `reason_code` operativo",
) -> str:
    tabla = "\n".join(filas)
    return textwrap.dedent(
        f"""
        # Documento

        {titulo}
        <!-- GATE_REASON_CODES_GLOSARIO:START -->
        | `reason_code` | Significado corto | Acción sugerida |
        | --- | --- | --- |
        {tabla}
        <!-- GATE_REASON_CODES_GLOSARIO:END -->
        """
    ).strip()


def test_glosario_reason_codes_sincronizado_con_codigo() -> None:
    ruta_doc = gate_pr.REPO_ROOT / "docs" / "ci_quality_gate.md"
    codigos_documentados = gate_pr.reason_codes_operativos_documentados_en_docs(ruta_doc)
    codigos_registrados = gate_pr.reason_codes_operativos_documentables()
    resultado = comparar_reason_codes(canonicos=codigos_registrados, documentados=codigos_documentados)
    assert resultado.en_sync


def test_parser_no_depende_del_titulo_humano() -> None:
    doc = _render_doc_glosario(
        (
            "| `TOOLCHAIN_LOCK_INVALIDO` | x | y |",
            "| `DEPENDENCIAS_FALTANTES` | x | y |",
        ),
        titulo="## Título editado por humanos",
    )
    codigos = extraer_reason_codes_documentados(doc)
    assert codigos == ("DEPENDENCIAS_FALTANTES", "TOOLCHAIN_LOCK_INVALIDO")


def test_parser_falla_si_glosario_no_tiene_marcadores() -> None:
    doc = "# Documento\n\n## Glosario\n| `reason_code` | a | b |"
    try:
        extraer_reason_codes_documentados(doc)
    except ErrorContratoReasonCodesDoc as exc:
        assert "marcador de inicio" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Se esperaba ErrorContratoReasonCodesDoc por glosario sin delimitadores.")


def test_comparador_reporta_faltantes_y_sobrantes() -> None:
    resultado = comparar_reason_codes(
        canonicos=("A", "B"),
        documentados=("B", "C"),
    )
    assert resultado.faltantes_en_doc == ("A",)
    assert resultado.sobrantes_en_doc == ("C",)


def test_check_documental_reutilizable_falla_con_detalle_claro(tmp_path) -> None:
    ruta_doc = tmp_path / "ci_quality_gate.md"
    ruta_doc.write_text(
        _render_doc_glosario(
            (
                "| `TOOLCHAIN_LOCK_INVALIDO` | x | y |",
                "| `EXTRA_DESCONOCIDO` | x | y |",
            )
        ),
        encoding="utf-8",
    )

    try:
        gate_pr.validar_contrato_reason_codes_doc(ruta_doc)
    except ErrorContratoReasonCodesDoc as exc:
        mensaje = str(exc)
        assert "Check documental reason_code falló" in mensaje
        assert "sin documentar" in mensaje
        assert "sin fuente canonica" in mensaje
        assert "EXTRA_DESCONOCIDO" in mensaje
    else:  # pragma: no cover
        raise AssertionError("Se esperaba ErrorContratoReasonCodesDoc por divergencia doc↔código.")


def test_parser_snippets_semantica_bloqueo_operativo_por_marcadores() -> None:
    doc = textwrap.dedent(
        """
        # Documento
        ## Sección editable
        <!-- GATE_BLOQUEO_OPERATIVO_SEMANTICA:START -->
        - `bloqueo operativo local`
        - `todavía no se validó el proyecto`
        <!-- GATE_BLOQUEO_OPERATIVO_SEMANTICA:END -->
        """
    ).strip()
    snippets = extraer_snippets_semantica_bloqueo_operativo(doc)
    assert snippets == ("bloqueo operativo local", "todavía no se validó el proyecto")


def test_parser_snippets_falla_si_bloque_semantico_no_existe() -> None:
    doc = "# Documento\n\nSin markers de semántica."
    try:
        extraer_snippets_semantica_bloqueo_operativo(doc)
    except ErrorContratoReasonCodesDoc as exc:
        assert "semántica mínima de bloqueo operativo" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Se esperaba ErrorContratoReasonCodesDoc por semántica sin delimitadores.")
