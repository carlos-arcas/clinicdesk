from __future__ import annotations

import pytest

from clinicdesk import __version__
from scripts import version


def test_version_main_emite_version_por_stdout(capsys) -> None:
    version.main()

    salida = capsys.readouterr()
    assert salida.out.strip() == __version__


def test_assert_tag_matches_version_ok() -> None:
    version.assert_tag_matches_version(tag=f"v{__version__}", version=__version__)


def test_assert_tag_matches_version_falla_por_mismatch() -> None:
    with pytest.raises(ValueError, match="no coincide"):
        version.assert_tag_matches_version(tag="v9.9.9", version=__version__)


def test_assert_tag_matches_version_falla_sin_prefijo_v() -> None:
    with pytest.raises(ValueError, match="iniciar con 'v'"):
        version.assert_tag_matches_version(tag=__version__, version=__version__)
