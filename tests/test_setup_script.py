from __future__ import annotations

from pathlib import Path

from scripts import setup


class _Resultado:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _DiagnosticoAlineado:
    herramientas = ()
    wheelhouse_disponible = False
    wheelhouse = Path("wheelhouse")
    python_activo = "3.12.0"
    venv_activo = True
    cache_pip = "/tmp/pip"
    indice_pip = None
    proxy_configurado = False
    diagnostico_red = "sin wheelhouse"
    tiene_faltantes = False
    tiene_desalineaciones = False
    toolchain_error = None
    source_of_truth = "requirements-dev.txt"


def _mockear_doctor_alineado(monkeypatch) -> None:
    monkeypatch.setattr(setup, "diagnosticar_entorno_calidad", lambda *_args, **_kwargs: _DiagnosticoAlineado())
    monkeypatch.setattr(setup, "renderizar_reporte", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(setup, "codigo_salida_estable", lambda *_args, **_kwargs: 0)


def test_setup_main_ejecuta_comandos_esperados(monkeypatch, tmp_path: Path) -> None:
    comandos: list[list[str]] = []
    venv_dir = tmp_path / ".venv"
    python_venv = venv_dir / "bin" / "python"
    original_exists = Path.exists

    def fake_run(command, **kwargs):
        comandos.append(command)
        return _Resultado(returncode=0, stdout="ok")

    monkeypatch.setattr(setup, "PROJECT_ROOT", Path(__file__).resolve().parents[1])
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: python_venv)
    _mockear_doctor_alineado(monkeypatch)
    monkeypatch.setattr(Path, "exists", lambda self: True if self == python_venv else original_exists(self))

    rc = setup.main()

    assert rc == 0
    assert [setup.sys.executable, "-m", "venv", str(venv_dir)] in comandos
    assert any(
        comando[1:] == ["-m", "pip", "install", "-r", str(setup.PROJECT_ROOT / "requirements.txt")]
        for comando in comandos
    )
    assert any(
        comando[1:] == ["-m", "pip", "install", "-r", str(setup.PROJECT_ROOT / "requirements-dev.txt")]
        for comando in comandos
    )


def test_setup_main_devuelve_error_si_falla_subproceso(monkeypatch, tmp_path: Path, capsys) -> None:
    venv_dir = tmp_path / ".venv"
    python_venv = venv_dir / "bin" / "python"
    original_exists = Path.exists

    def fake_run(command, **kwargs):
        if command[-1].endswith("requirements.txt"):
            return _Resultado(returncode=1, stderr="connection timed out")
        return _Resultado(returncode=0, stdout="ok")

    monkeypatch.setattr(setup, "PROJECT_ROOT", Path(__file__).resolve().parents[1])
    monkeypatch.setattr(setup, "VENV_DIR", venv_dir)
    monkeypatch.setattr(setup.subprocess, "run", fake_run)
    monkeypatch.setattr(setup, "_venv_python", lambda: python_venv)
    _mockear_doctor_alineado(monkeypatch)
    monkeypatch.setattr(Path, "exists", lambda self: True if self == python_venv else original_exists(self))

    rc = setup.main()

    salida = capsys.readouterr().out
    assert rc == 1
    assert "[setup][error]" in salida
    assert "Instalar dependencias runtime" in salida
    assert "entorno no es recuperable localmente" in salida


def test_instalar_dependencias_falla_si_falta_requirements(monkeypatch, tmp_path: Path) -> None:
    python_venv = tmp_path / "bin" / "python"
    original_exists = Path.exists

    monkeypatch.setattr(setup, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        Path,
        "exists",
        lambda self: False
        if self in {tmp_path / "requirements.txt", tmp_path / "requirements-dev.txt"}
        else original_exists(self),
    )

    try:
        setup._instalar_dependencias(python_venv)
    except RuntimeError as exc:
        assert "No se encontraron requirements.txt" in str(exc)
    else:
        raise AssertionError("Se esperaba RuntimeError cuando faltan requirements")


def test_resumen_error_instalacion_detecta_proxy() -> None:
    lineas = setup._resumen_error_instalacion("ProxyError: tunnel connection failed", "")
    assert any("red/proxy" in linea for linea in lineas)
