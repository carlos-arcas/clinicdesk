from __future__ import annotations

from clinicdesk import __version__
from scripts import version


def test_version_main_emite_version_por_stdout(capsys) -> None:
    version.main()

    salida = capsys.readouterr()
    assert salida.out.strip() == __version__
