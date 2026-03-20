from __future__ import annotations

from types import SimpleNamespace

from scripts import gate_pr


def test_gate_pr_aborta_si_el_entorno_esta_bloqueado(monkeypatch, capsys) -> None:
    monkeypatch.setattr(gate_pr, "_preflight_entorno", lambda _repo_root: gate_pr.EXIT_ENTORNO_BLOQUEADO)
    ejecuciones: list[list[str]] = []

    def _run_mock(comando, **_kwargs):
        ejecuciones.append(comando)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(gate_pr.subprocess, "run", _run_mock)

    rc = gate_pr.main()

    assert rc == gate_pr.EXIT_ENTORNO_BLOQUEADO
    assert ejecuciones == []
    assert capsys.readouterr().err == ""


def test_gate_pr_ejecuta_quality_gate_si_preflight_esta_ok(monkeypatch) -> None:
    monkeypatch.setattr(gate_pr, "_preflight_entorno", lambda _repo_root: 0)
    ejecuciones: list[list[str]] = []

    def _run_mock(comando, **_kwargs):
        ejecuciones.append(comando)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(gate_pr.subprocess, "run", _run_mock)

    rc = gate_pr.main()

    assert rc == 7
    assert ejecuciones == [[gate_pr.sys.executable, "scripts/quality_gate.py", "--strict"]]
