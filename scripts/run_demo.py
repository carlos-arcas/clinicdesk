from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.diagnostico_helpers import escribir_json, escribir_texto, primeras_lineas_redactadas

NOMBRE_MODULO_APP = "clinicdesk.app.main"
RUTA_DB_DEMO = Path("data/demo/clinicdesk_demo.db")
MAX_LINEAS_DIAGNOSTICO = 200


def _resolver_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Siembra datos demo y arranca ClinicDesk en demo mode.")
    parser.add_argument("--skip-seed", action="store_true", help="No ejecutar seed_demo_data.py antes de arrancar.")
    parser.add_argument("--no-reset", action="store_true", help="No pasar --reset al proceso de siembra.")
    parser.add_argument("--seed", type=int, help="Seed para el generador de datos demo.")
    parser.add_argument("--doctors", type=int, help="Cantidad de doctores demo.")
    parser.add_argument("--patients", type=int, help="Cantidad de pacientes demo.")
    parser.add_argument("--appointments", type=int, help="Cantidad de citas demo.")
    return parser


def _build_seed_command(args: argparse.Namespace, ruta_db: str) -> list[str]:
    comando = [
        sys.executable,
        "seed_demo_data.py",
        "--sqlite-path",
        ruta_db,
    ]
    if not args.no_reset:
        comando.append("--reset")
    if args.seed is not None:
        comando.extend(["--seed", str(args.seed)])
    if args.doctors is not None:
        comando.extend(["--doctors", str(args.doctors)])
    if args.patients is not None:
        comando.extend(["--patients", str(args.patients)])
    if args.appointments is not None:
        comando.extend(["--appointments", str(args.appointments)])
    return comando


def _build_env(repo_root: Path) -> tuple[dict[str, str], str]:
    env = os.environ.copy()
    ruta_db_default = str((repo_root / RUTA_DB_DEMO).resolve())
    ruta_db = env.get("CLINICDESK_DB_PATH", ruta_db_default)
    env["CLINICDESK_DB_PATH"] = ruta_db
    if "PYTHONPATH" not in env:
        env["PYTHONPATH"] = "."
    return env, ruta_db


def _run_subprocess(
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, check=False, capture_output=True, text=True)


def _resolver_ruta_logs(repo_root: Path) -> Path:
    ruta_logs = repo_root / "logs"
    ruta_logs.mkdir(parents=True, exist_ok=True)
    return ruta_logs


def _guardar_logs_subproceso(ruta_logs: Path, prefijo: str, resultado: subprocess.CompletedProcess[str] | None) -> None:
    stdout = "" if resultado is None else (resultado.stdout or "")
    stderr = "" if resultado is None else (resultado.stderr or "")
    escribir_texto(ruta_logs / f"demo_{prefijo}_stdout.log", stdout)
    escribir_texto(ruta_logs / f"demo_{prefijo}_stderr.log", stderr)


def _crear_failure_summary(
    *,
    ruta_logs: Path,
    ruta_db: str,
    comando_seed: list[str],
    comando_app: list[str],
    resultado_seed: subprocess.CompletedProcess[str] | None,
    resultado_app: subprocess.CompletedProcess[str] | None,
    reason_code: str,
) -> None:
    resumen = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "db_path": ruta_db,
        "comando_seed": comando_seed,
        "comando_app": comando_app,
        "returncodes": {
            "seed": None if resultado_seed is None else resultado_seed.returncode,
            "app": None if resultado_app is None else resultado_app.returncode,
        },
        "stdout_lineas": {
            "seed": primeras_lineas_redactadas(
                "" if resultado_seed is None else (resultado_seed.stdout or ""),
                max_lineas=MAX_LINEAS_DIAGNOSTICO,
            ),
            "app": primeras_lineas_redactadas(
                "" if resultado_app is None else (resultado_app.stdout or ""),
                max_lineas=MAX_LINEAS_DIAGNOSTICO,
            ),
        },
        "stderr_lineas": {
            "seed": primeras_lineas_redactadas(
                "" if resultado_seed is None else (resultado_seed.stderr or ""),
                max_lineas=MAX_LINEAS_DIAGNOSTICO,
            ),
            "app": primeras_lineas_redactadas(
                "" if resultado_app is None else (resultado_app.stderr or ""),
                max_lineas=MAX_LINEAS_DIAGNOSTICO,
            ),
        },
        "reason_code": reason_code,
    }
    escribir_json(ruta_logs / "demo_failure_summary.json", resumen)


def _limpiar_failure_summary_si_existe(ruta_logs: Path) -> None:
    # Política elegida: en ejecución exitosa se elimina el resumen previo para evitar diagnósticos obsoletos.
    ruta_summary = ruta_logs / "demo_failure_summary.json"
    if ruta_summary.exists():
        ruta_summary.unlink()


def main(argv: list[str] | None = None) -> int:
    args = _crear_parser().parse_args(argv)
    repo_root = _resolver_repo_root()
    os.chdir(repo_root)
    env, ruta_db = _build_env(repo_root)
    ruta_logs = _resolver_ruta_logs(repo_root)
    comando_seed = _build_seed_command(args, ruta_db)
    comando_app = [sys.executable, "-m", NOMBRE_MODULO_APP]
    resultado_seed: subprocess.CompletedProcess[str] | None = None
    resultado_app: subprocess.CompletedProcess[str] | None = None

    try:
        if not args.skip_seed:
            sys.stdout.write(f"[run_demo] Sembrando datos demo en: {ruta_db}\n")
            resultado_seed = _run_subprocess(comando_seed, cwd=repo_root, env=env)
            _guardar_logs_subproceso(ruta_logs, "seed", resultado_seed)
            if resultado_seed.returncode != 0:
                _guardar_logs_subproceso(ruta_logs, "app", None)
                _crear_failure_summary(
                    ruta_logs=ruta_logs,
                    ruta_db=ruta_db,
                    comando_seed=comando_seed,
                    comando_app=comando_app,
                    resultado_seed=resultado_seed,
                    resultado_app=None,
                    reason_code="seed_failed",
                )
                sys.stderr.write(f"[run_demo] Seed falló con código {resultado_seed.returncode}\n")
                return resultado_seed.returncode
        else:
            _guardar_logs_subproceso(ruta_logs, "seed", None)

        sys.stdout.write("[run_demo] Arrancando app en modo demo...\n")
        resultado_app = _run_subprocess(comando_app, cwd=repo_root, env=env)
        _guardar_logs_subproceso(ruta_logs, "app", resultado_app)
        if resultado_app.returncode != 0:
            _crear_failure_summary(
                ruta_logs=ruta_logs,
                ruta_db=ruta_db,
                comando_seed=comando_seed,
                comando_app=comando_app,
                resultado_seed=resultado_seed,
                resultado_app=resultado_app,
                reason_code="app_failed",
            )
        if resultado_app.returncode == 0:
            _limpiar_failure_summary_si_existe(ruta_logs)
        return resultado_app.returncode
    except OSError as exc:
        _guardar_logs_subproceso(ruta_logs, "seed", resultado_seed)
        _guardar_logs_subproceso(ruta_logs, "app", resultado_app)
        _crear_failure_summary(
            ruta_logs=ruta_logs,
            ruta_db=ruta_db,
            comando_seed=comando_seed,
            comando_app=comando_app,
            resultado_seed=resultado_seed,
            resultado_app=resultado_app,
            reason_code="os_error",
        )
        sys.stderr.write(f"[run_demo] Error operativo al lanzar procesos: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
