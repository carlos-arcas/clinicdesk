from __future__ import annotations

from pathlib import Path

from scripts import gate_pr


def _reason_codes_documentados_en_glosario(ruta_doc: Path) -> tuple[str, ...]:
    lineas = ruta_doc.read_text(encoding="utf-8").splitlines()
    inicio = lineas.index("## Glosario breve de `reason_code` operativo")
    codigos: list[str] = []
    for linea in lineas[inicio + 1 :]:
        if linea.startswith("## "):
            break
        if not linea.startswith("| `"):
            continue
        partes = [parte.strip() for parte in linea.split("|")]
        if len(partes) < 3:
            continue
        codigo = partes[1].strip("`")
        if codigo == "reason_code":
            continue
        codigos.append(codigo)
    return tuple(sorted(codigos))


def test_glosario_reason_codes_sincronizado_con_codigo() -> None:
    ruta_doc = gate_pr.REPO_ROOT / "docs" / "ci_quality_gate.md"
    codigos_documentados = _reason_codes_documentados_en_glosario(ruta_doc)
    codigos_registrados = gate_pr.reason_codes_operativos_documentables()
    assert codigos_documentados == codigos_registrados
