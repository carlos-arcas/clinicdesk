from __future__ import annotations

from scripts import format_all


class _ProcesoFalso:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def test_main_invoca_format_py_y_no_ruff_directo(monkeypatch) -> None:
    observado: dict[str, object] = {}

    monkeypatch.setattr(format_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(format_all.os, "chdir", lambda path: observado.setdefault("cwd", path))

    def fake_run(comando, check):
        observado["comando"] = list(comando)
        return _ProcesoFalso(returncode=0)

    mensajes: list[str] = []
    monkeypatch.setattr(format_all.subprocess, "run", fake_run)
    monkeypatch.setattr(format_all.LOGGER, "info", lambda mensaje: mensajes.append(mensaje))

    rc = format_all.main()

    assert rc == 0
    assert observado["cwd"] == "/tmp/repo"
    assert observado["comando"] == [
        format_all.sys.executable,
        "-m",
        "scripts.format_py",
    ]
    assert "ruff" not in " ".join(observado["comando"])
    assert mensajes == ["format_py ejecutado; markdown/yaml no se formatean aquí"]


def test_main_propaga_returncode(monkeypatch) -> None:
    monkeypatch.setattr(format_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(format_all.os, "chdir", lambda *_: None)
    monkeypatch.setattr(
        format_all.subprocess,
        "run",
        lambda *_args, **_kwargs: _ProcesoFalso(returncode=9),
    )

    assert format_all.main() == 9
