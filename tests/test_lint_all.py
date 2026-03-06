from __future__ import annotations

from pathlib import Path

from scripts import lint_all


class _ProcesoFalso:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def test_main_invoca_lint_y_structural_en_orden(monkeypatch) -> None:
    comandos: list[list[str]] = []
    monkeypatch.setattr(lint_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(lint_all.os, "chdir", lambda *_: None)
    monkeypatch.setattr(lint_all, "_validar_workflows_yaml", lambda *_: 0)

    def fake_run(comando, check):
        comandos.append(list(comando))
        return _ProcesoFalso(returncode=0)

    monkeypatch.setattr(lint_all.subprocess, "run", fake_run)

    rc = lint_all.main()

    assert rc == 0
    assert comandos == [
        [lint_all.sys.executable, "-m", "scripts.lint_py"],
        [lint_all.sys.executable, "-m", "scripts.structural_gate"],
    ]


def test_main_prioriza_returncode_de_lint(monkeypatch) -> None:
    monkeypatch.setattr(lint_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(lint_all.os, "chdir", lambda *_: None)
    monkeypatch.setattr(lint_all, "_validar_workflows_yaml", lambda *_: 0)

    resultados = iter([5, 0])

    def fake_run(_comando, check):
        return _ProcesoFalso(returncode=next(resultados))

    monkeypatch.setattr(lint_all.subprocess, "run", fake_run)

    assert lint_all.main() == 5


def test_main_retorna_structural_si_lint_ok(monkeypatch) -> None:
    monkeypatch.setattr(lint_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(lint_all.os, "chdir", lambda *_: None)
    monkeypatch.setattr(lint_all, "_validar_workflows_yaml", lambda *_: 0)

    resultados = iter([0, 7])

    def fake_run(_comando, check):
        return _ProcesoFalso(returncode=next(resultados))

    monkeypatch.setattr(lint_all.subprocess, "run", fake_run)

    assert lint_all.main() == 7


def test_main_retorna_yaml_si_lint_y_structural_ok(monkeypatch) -> None:
    monkeypatch.setattr(lint_all, "resolver_repo_root", lambda: "/tmp/repo")
    monkeypatch.setattr(lint_all.os, "chdir", lambda *_: None)
    monkeypatch.setattr(lint_all, "_validar_workflows_yaml", lambda *_: 4)
    monkeypatch.setattr(
        lint_all.subprocess,
        "run",
        lambda *_args, **_kwargs: _ProcesoFalso(returncode=0),
    )

    assert lint_all.main() == 4


def test_validar_workflows_yaml_salta_si_no_hay_pyyaml(monkeypatch, tmp_path: Path) -> None:
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "yaml":
            raise ImportError
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    mensajes: list[str] = []
    monkeypatch.setattr(lint_all.LOGGER, "info", lambda mensaje: mensajes.append(mensaje))

    rc = lint_all._validar_workflows_yaml(tmp_path)

    assert rc == 0
    assert mensajes == ["PyYAML no disponible, saltando yaml validation"]
