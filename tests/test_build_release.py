from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from scripts.build_release import construir_release_bundle


def _write_file(path: Path, content: str = "contenido") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_release_generates_zip_and_manifest(tmp_path: Path) -> None:
    _write_file(tmp_path / "clinicdesk" / "__init__.py", '__version__ = "0.1.0"\n')
    _write_file(tmp_path / "clinicdesk" / "app.py")
    _write_file(tmp_path / "scripts" / "run_app.py")
    _write_file(tmp_path / "requirements.txt")
    _write_file(tmp_path / "requirements-dev.txt")
    _write_file(tmp_path / "README.md")
    _write_file(tmp_path / "docs" / "security_hardening.md")
    _write_file(tmp_path / "docs" / "security_keys.md")

    _write_file(tmp_path / "clinicdesk" / "__pycache__" / "cache.pyc")
    _write_file(tmp_path / "scripts" / "logs" / "runtime.log")
    _write_file(tmp_path / "data" / "local.sqlite")
    _write_file(tmp_path / "clinicdesk" / "data" / "clinic.db")

    zip_path = construir_release_bundle(tmp_path)

    assert zip_path.exists()

    with ZipFile(zip_path) as zipf:
        nombres = set(zipf.namelist())
        assert "MANIFEST.json" in nombres

        manifest = json.loads(zipf.read("MANIFEST.json").decode("utf-8"))
        assert manifest["version"] == "0.1.0"
        assert "built_at_utc" in manifest
        assert "python_version" in manifest

        assert "clinicdesk/app.py" in nombres
        assert "scripts/run_app.py" in nombres
        assert "docs/security_hardening.md" in nombres
        assert "docs/security_keys.md" in nombres

        prohibidos = ("__pycache__", ".pyc", "/logs/", "/data/", ".sqlite", ".db")
        for nombre in nombres:
            assert not any(p in nombre for p in prohibidos), nombre


def test_main_emite_ruta_zip_por_stdout(tmp_path: Path, monkeypatch, capsys) -> None:
    _write_file(tmp_path / "clinicdesk" / "__init__.py", '__version__ = "0.1.0"\n')
    _write_file(tmp_path / "clinicdesk" / "app.py")
    _write_file(tmp_path / "scripts" / "run_app.py")
    _write_file(tmp_path / "requirements.txt")
    _write_file(tmp_path / "requirements-dev.txt")
    _write_file(tmp_path / "README.md")
    _write_file(tmp_path / "docs" / "security_hardening.md")
    _write_file(tmp_path / "docs" / "security_keys.md")

    monkeypatch.chdir(tmp_path)

    from scripts.build_release import main

    main()

    salida = capsys.readouterr()
    assert salida.out.strip().startswith("zip generado: ")
    assert "clinicdesk-" in salida.out
