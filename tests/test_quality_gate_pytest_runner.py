from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.quality_gate_components import entrypoint, pytest_and_coverage


class _ProcessResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _import_coverage_ok(_: str) -> object:
    return object()


def _import_coverage_missing(_: str) -> object:
    raise ModuleNotFoundError("No module named 'coverage'")


def test_run_pytest_with_coverage_desactiva_autoload(monkeypatch):
    llamadas: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, check, env):
        llamadas.append((list(cmd), dict(env)))
        return _ProcessResult()

    previo = os.environ.get("PYTEST_ADDOPTS")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-p pytestqt")
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_ok)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)

    exit_code = pytest_and_coverage.run_pytest_with_coverage(["-q", "-m", "not ui"])

    assert exit_code == 0
    assert llamadas[0][0] == [pytest_and_coverage.sys.executable, "-m", "coverage", "erase"]
    assert llamadas[1][0] == [
        pytest_and_coverage.sys.executable,
        "-m",
        "coverage",
        "run",
        "-m",
        "pytest",
        "-q",
        "-m",
        "not ui",
    ]
    assert llamadas[1][1]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert llamadas[1][1]["PYTEST_ADDOPTS"] == ""
    assert os.environ.get("PYTEST_ADDOPTS") == "-p pytestqt"
    if previo is None:
        assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" not in os.environ


def test_run_pytest_core_con_coverage_ejecuta_flujo(monkeypatch):
    llamadas: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, check, env):
        llamadas.append((list(cmd), dict(env)))
        return _ProcessResult()

    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_ok)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)
    monkeypatch.setattr(pytest_and_coverage, "compute_core_coverage", lambda core_paths=None: 91.25)

    coverage = pytest_and_coverage.run_pytest_core_con_coverage(["-q", "-m", "not ui"])

    assert coverage == 91.25
    assert llamadas[1][0][-3:] == ["-q", "-m", "not ui"]
    assert "uiqt" not in " ".join(llamadas[1][0])
    assert llamadas[1][1]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert llamadas[2][0][:4] == [pytest_and_coverage.sys.executable, "-m", "coverage", "xml"]
    assert llamadas[3][0][:4] == [pytest_and_coverage.sys.executable, "-m", "coverage", "json"]


def test_run_pytest_core_con_coverage_en_sandbox_ejecuta_pytest_simple(monkeypatch):
    llamadas: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(cmd, check, env):
        llamadas.append((list(cmd), dict(env)))
        return _ProcessResult()

    monkeypatch.setenv("CLINICDESK_SANDBOX_MODE", "1")
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_missing)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)

    coverage = pytest_and_coverage.run_pytest_core_con_coverage(["-q", "-m", "not ui"])

    assert coverage == 0.0
    assert len(llamadas) == 1
    assert llamadas[0][0] == [pytest_and_coverage.sys.executable, "-m", "pytest", "-q", "-m", "not ui"]


def test_run_test_and_coverage_usa_selector_core(monkeypatch):
    observado_args: list[list[str]] = []

    def fake_run_core(pytest_args):
        observado_args.append(list(pytest_args))
        return 90.0

    monkeypatch.setattr(entrypoint, "run_pytest_core_con_coverage", fake_run_core)

    assert entrypoint._run_test_and_coverage() == 0
    assert observado_args == [entrypoint.CORE_PYTEST_ARGS]
    assert "uiqt" not in " ".join(observado_args[0])


def test_run_test_and_coverage_omite_umbral_en_sandbox(monkeypatch, caplog):
    monkeypatch.setattr(entrypoint, "run_pytest_core_con_coverage", lambda pytest_args: 0.0)
    monkeypatch.setattr(entrypoint, "omitir_coverage_por_sandbox", lambda: True)

    with caplog.at_level("WARNING"):
        rc = entrypoint._run_test_and_coverage()

    assert rc == 0
    assert "Cobertura omitida por dependencia faltante" in caplog.text


def test_compute_core_coverage_lee_resumen_json(monkeypatch, tmp_path: Path):
    reporte = tmp_path / "docs" / "coverage.json"
    reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.write_text(
        json.dumps(
            {"files": {"clinicdesk/app/domain/enums.py": {"summary": {"num_statements": 4, "covered_lines": 3}}}}
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(pytest_and_coverage.config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        pytest_and_coverage,
        "iter_core_files",
        lambda core_paths=None: [tmp_path / "clinicdesk" / "app" / "domain" / "enums.py"],
    )

    coverage = pytest_and_coverage.compute_core_coverage()

    assert coverage == 75.0


def test_run_pytest_with_coverage_falla_controlado_si_falta_modulo(monkeypatch, caplog):
    llamadas: list[list[str]] = []

    def fake_run(cmd, check, env):
        llamadas.append(list(cmd))
        return _ProcessResult()

    monkeypatch.delenv("CLINICDESK_SANDBOX_MODE", raising=False)
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_missing)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        rc = pytest_and_coverage.run_pytest_with_coverage(["-q", "-m", "not ui"])

    assert rc == pytest_and_coverage.RC_DEPENDENCIA_FALTANTE
    assert "Falta dependencia 'coverage'" in caplog.text
    assert llamadas == []


def test_run_pytest_with_coverage_omite_check_si_sandbox_y_falta_modulo(monkeypatch, caplog):
    llamadas: list[list[str]] = []

    def fake_run(cmd, check, env):
        llamadas.append(list(cmd))
        return _ProcessResult()

    monkeypatch.setenv("CLINICDESK_SANDBOX_MODE", "1")
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_missing)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)

    with caplog.at_level("WARNING"):
        rc = pytest_and_coverage.run_pytest_with_coverage(["-q", "-m", "not ui"])

    assert rc == 0
    assert "coverage no disponible" in caplog.text
    assert "CLINICDESK_SANDBOX_MODE=1" in caplog.text
    assert llamadas == []


def test_run_coverage_report_falla_controlado_si_falta_modulo(monkeypatch, caplog):
    llamadas: list[list[str]] = []

    def fake_run(cmd, check, env):
        llamadas.append(list(cmd))
        return _ProcessResult()

    monkeypatch.delenv("CLINICDESK_SANDBOX_MODE", raising=False)
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_missing)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)

    with caplog.at_level("ERROR"):
        rc = pytest_and_coverage.run_coverage_report()

    assert rc == pytest_and_coverage.RC_DEPENDENCIA_FALTANTE
    assert "Falta dependencia 'coverage'" in caplog.text
    assert llamadas == []


def test_run_pytest_with_coverage_genera_diagnostico_en_255_si_env_activa(monkeypatch, tmp_path: Path):
    logs_dir = tmp_path / "logs"

    def fake_run(cmd, check, env, **kwargs):
        if cmd[:4] == [pytest_and_coverage.sys.executable, "-m", "coverage", "erase"]:
            return _ProcessResult(returncode=0)
        return _ProcessResult(
            returncode=255,
            stdout="\n".join([f"linea {i}" for i in range(130)]),
            stderr="email paciente@example.com\nDNI 12345678Z",
        )

    monkeypatch.setenv("CLINICDESK_DIAGNOSTICO_PYTEST_255", "1")
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_ok)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)
    monkeypatch.setattr(pytest_and_coverage.config, "REPO_ROOT", tmp_path)

    rc = pytest_and_coverage.run_pytest_with_coverage(["-q", "-m", "not ui"])

    assert rc == 255
    assert logs_dir.joinpath("pytest_stdout.log").exists()
    assert logs_dir.joinpath("pytest_stderr.log").exists()
    resumen = json.loads(logs_dir.joinpath("pytest_failure_summary.json").read_text(encoding="utf-8"))
    assert len(resumen["stdout_lineas"]) == 120
    assert "paciente@example.com" not in "\n".join(resumen["stderr_lineas"])
    assert "12345678Z" not in "\n".join(resumen["stderr_lineas"])


def test_run_pytest_with_coverage_no_genera_diagnostico_si_env_inactiva(monkeypatch, tmp_path: Path):
    logs_dir = tmp_path / "logs"

    def fake_run(cmd, check, env, **kwargs):
        if cmd[:4] == [pytest_and_coverage.sys.executable, "-m", "coverage", "erase"]:
            return _ProcessResult(returncode=0)
        return _ProcessResult(returncode=255, stdout="fallo", stderr="error")

    monkeypatch.delenv("CLINICDESK_DIAGNOSTICO_PYTEST_255", raising=False)
    monkeypatch.setattr(pytest_and_coverage.importlib, "import_module", _import_coverage_ok)
    monkeypatch.setattr(pytest_and_coverage.subprocess, "run", fake_run)
    monkeypatch.setattr(pytest_and_coverage.config, "REPO_ROOT", tmp_path)

    rc = pytest_and_coverage.run_pytest_with_coverage(["-q", "-m", "not ui"])

    assert rc == 255
    assert not logs_dir.joinpath("pytest_failure_summary.json").exists()
