from __future__ import annotations

from types import SimpleNamespace

from scripts import gate_pr
from scripts.quality_gate_components.ejecucion_canonica import DecisionEjecucionCanonica


def test_gate_pr_aborta_si_el_entorno_esta_bloqueado(monkeypatch, capsys) -> None:
    monkeypatch.setattr(gate_pr, "_preflight_entorno", lambda _repo_root: gate_pr.EXIT_ENTORNO_BLOQUEADO)
    monkeypatch.setattr(gate_pr, "resolver_ejecucion_canonica", lambda *_args, **_kwargs: DecisionEjecucionCanonica("continuar"))
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
    monkeypatch.setattr(gate_pr, "resolver_ejecucion_canonica", lambda *_args, **_kwargs: DecisionEjecucionCanonica("continuar"))
    ejecuciones: list[list[str]] = []

    def _run_mock(comando, **_kwargs):
        ejecuciones.append(comando)
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(gate_pr.subprocess, "run", _run_mock)

    rc = gate_pr.main()

    assert rc == 7
    assert ejecuciones == [[gate_pr.sys.executable, "scripts/quality_gate.py", "--strict"]]


def test_gate_pr_reejecuta_en_python_del_repo(monkeypatch) -> None:
    monkeypatch.setattr(
        gate_pr,
        "resolver_ejecucion_canonica",
        lambda *_args, **_kwargs: DecisionEjecucionCanonica("reejecutar", python_objetivo=gate_pr.REPO_ROOT / ".venv" / "bin" / "python"),
    )
    observado = {}
    monkeypatch.setattr(gate_pr, "reejecutar_en_python_objetivo", lambda decision, argv: observado.update({"decision": decision, "argv": argv}) or 9)

    rc = gate_pr.main()

    assert rc == 9
    assert observado["argv"][:2] == ["-m", "scripts.gate_pr"]


def test_preflight_entorno_explica_rc_20(monkeypatch, capsys) -> None:
    class _Interprete:
        usa_python_repo = False

    class _Diag:
        toolchain_error = None
        herramientas = ()
        wheelhouse_disponible = False
        wheelhouse = None
        python_activo = "3.12.0"
        python_path = "/tmp/python"
        venv_activo = False
        cache_pip = None
        indice_pip = None
        proxy_configurado = False
        diagnostico_red = "sin wheelhouse"
        source_of_truth = "requirements-dev.txt"
        tiene_faltantes = True
        tiene_desalineaciones = False
        entorno_bloqueado = True
        interprete = _Interprete()

    monkeypatch.setattr(gate_pr, "diagnosticar_entorno_calidad", lambda _root: _Diag())
    monkeypatch.setattr(gate_pr, "codigo_salida_estable", lambda _diag: 2)
    monkeypatch.setattr(
        gate_pr,
        "clasificar_bloqueo_entorno",
        lambda _diag: SimpleNamespace(
            reason_code="DEPENDENCIAS_FALTANTES",
            categoria="toolchain",
            detalle="Faltan herramientas del gate en el intérprete activo.",
            accion_sugerida="python -m pip install -r requirements-dev.txt",
        ),
    )
    monkeypatch.setattr(gate_pr, "renderizar_reporte", lambda _diag: ["[doctor][error] ruff ausente"])

    rc = gate_pr._preflight_entorno(gate_pr.REPO_ROOT)

    err = capsys.readouterr().err
    assert rc == gate_pr.EXIT_ENTORNO_BLOQUEADO
    assert "rc=20" in err
    assert "todavía no se validó el proyecto" in err
    assert "reason_code=DEPENDENCIAS_FALTANTES" in err
    assert "Validaciones no ejecutadas" in err
    assert "scripts/setup.py" in err
