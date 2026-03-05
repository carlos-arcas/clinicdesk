from __future__ import annotations

import os

from scripts.quality_gate_components import entrypoint, pytest_and_coverage


class _TracerFalso:
    def __init__(self, observed_args: list[list[str]], observed_env: list[tuple[str | None, str | None]]):
        self._observed_args = observed_args
        self._observed_env = observed_env

    def runfunc(self, fn, pytest_args):
        self._observed_args.append(list(pytest_args))
        self._observed_env.append(
            (
                os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD"),
                os.environ.get("PYTEST_ADDOPTS"),
            )
        )
        return 0


class _CoverageTracerFalso:
    class _Resultados:
        counts: dict[tuple[str, int], int] = {}

    def results(self):
        return self._Resultados()


def test_run_pytest_with_trace_desactiva_autoload(monkeypatch):
    observed_args: list[list[str]] = []
    observed_env: list[tuple[str | None, str | None]] = []

    monkeypatch.setenv("PYTEST_ADDOPTS", "-p pytestqt")
    monkeypatch.setattr(
        pytest_and_coverage.trace,
        "Trace",
        lambda **kwargs: _TracerFalso(observed_args, observed_env),
    )

    exit_code, _tracer = pytest_and_coverage.run_pytest_with_trace(["-q", "-m", "not ui"])

    assert exit_code == 0
    assert observed_args == [["-q", "-m", "not ui"]]
    assert observed_env == [("1", "")]
    assert os.environ.get("PYTEST_ADDOPTS") == "-p pytestqt"
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" not in os.environ


def test_run_test_and_coverage_usa_selector_core(monkeypatch):
    observado_args: list[list[str]] = []

    def fake_run_pytest(pytest_args):
        observado_args.append(list(pytest_args))
        return 0, _CoverageTracerFalso()

    monkeypatch.setattr(entrypoint, "run_pytest_with_trace", fake_run_pytest)
    monkeypatch.setattr(entrypoint, "compute_core_coverage", lambda tracer: 90.0)
    monkeypatch.setattr(entrypoint, "run_coverage_report", lambda tracer, coverage: 0)

    assert entrypoint._run_test_and_coverage() == 0
    assert observado_args == [entrypoint.CORE_PYTEST_ARGS]
    assert "uiqt" not in " ".join(observado_args[0])
