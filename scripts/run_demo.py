from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


NOMBRE_MODULO_APP = "clinicdesk.app.main"
RUTA_DB_DEMO = Path("data/demo/clinicdesk_demo.db")


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


def _run_subprocess(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, env=env, check=False)


def main(argv: list[str] | None = None) -> int:
    args = _crear_parser().parse_args(argv)
    repo_root = _resolver_repo_root()
    os.chdir(repo_root)
    env, ruta_db = _build_env(repo_root)

    try:
        if not args.skip_seed:
            print(f"[run_demo] Sembrando datos demo en: {ruta_db}")
            seed_cmd = _build_seed_command(args, ruta_db)
            seed_result = _run_subprocess(seed_cmd, cwd=repo_root, env=env)
            if seed_result.returncode != 0:
                print(f"[run_demo] Seed falló con código {seed_result.returncode}", file=sys.stderr)
                return seed_result.returncode

        print("[run_demo] Arrancando app en modo demo...")
        app_cmd = [sys.executable, "-m", NOMBRE_MODULO_APP]
        app_result = _run_subprocess(app_cmd, cwd=repo_root, env=env)
        return app_result.returncode
    except OSError as exc:
        print(f"[run_demo] Error operativo al lanzar procesos: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
