from __future__ import annotations

from pathlib import Path

from scripts.verificar_inventario_legacy_repo import verificar


def _escribir_inventario(path: Path, rutas: list[str]) -> None:
    lineas = [
        "# Inventario",
        "",
        "| Ruta | Estado | Motivo | Dependencia activa desde /src | Acción recomendada |",
        "|---|---|---|---|---|",
    ]
    for ruta in rutas:
        lineas.append(f"| `{ruta}` | ARCHIVADO | test | NO | test |")
    path.write_text("\n".join(lineas), encoding="utf-8")


def test_inventario_presente_y_carpetas_listadas_pasa(tmp_path: Path) -> None:
    legacy = tmp_path / "repositorio" / "src" / "legacy" / "graveyard"
    legacy.mkdir(parents=True)
    inventario = tmp_path / "docs" / "audit"
    inventario.mkdir(parents=True)
    _escribir_inventario(inventario / "legacy_repo_inventory_final.md", ["repositorio/src/legacy/graveyard"])

    detectadas, faltantes = verificar(tmp_path)

    assert "repositorio/src/legacy/graveyard" in detectadas
    assert faltantes == []


def test_carpeta_legacy_no_listada_falla(tmp_path: Path) -> None:
    legacy = tmp_path / "repositorio" / "src" / "legacy" / "graveyard"
    legacy.mkdir(parents=True)
    inventario = tmp_path / "docs" / "audit"
    inventario.mkdir(parents=True)
    _escribir_inventario(inventario / "legacy_repo_inventory_final.md", ["repositorio/src/legacy/otro"])

    _, faltantes = verificar(tmp_path)

    assert "repositorio/src/legacy/graveyard" in faltantes
