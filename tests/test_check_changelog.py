from __future__ import annotations

from pathlib import Path

import pytest

from scripts import check_changelog as script
from scripts.check_changelog import check_changelog


def _escribir(path: Path, contenido: str) -> None:
    path.write_text(contenido, encoding="utf-8")


def test_check_changelog_ok_con_bullet_en_added(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    _escribir(
        changelog,
        """# Changelog

## [0.1.0] - 2026-03-04
### Added
- Nuevo flujo de release.
""",
    )

    check_changelog(path=changelog, version="0.1.0")


def test_check_changelog_falla_si_no_hay_seccion_de_version(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    _escribir(
        changelog,
        """# Changelog

## [0.0.9] - 2026-03-01
### Added
- Algo previo.
""",
    )

    with pytest.raises(ValueError, match="sección para la versión actual"):
        check_changelog(path=changelog, version="0.1.0")


def test_check_changelog_falla_si_seccion_esta_vacia(tmp_path: Path) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    _escribir(
        changelog,
        """# Changelog

## [0.1.0] - 2026-03-04
### Added
Sin bullets.
### Fixed
""",
    )

    with pytest.raises(ValueError, match="al menos un bullet"):
        check_changelog(path=changelog, version="0.1.0")


def test_main_check_valida_archivo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    changelog = tmp_path / "CHANGELOG.md"
    _escribir(
        changelog,
        """# Changelog

## [0.1.0] - 2026-03-04
### Fixed
- Ajuste de workflow.
""",
    )
    monkeypatch.setattr(
        "sys.argv",
        ["check_changelog", "--check", "--path", str(changelog), "--version", "0.1.0"],
    )

    assert script.main() == 0
