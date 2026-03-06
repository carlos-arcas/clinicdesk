"""Comando canónico de lint para Python y chequeos estructurales del repositorio."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from ._ruff_targets import resolver_repo_root

LOGGER = logging.getLogger(__name__)


def _ejecutar_comando(comando: list[str]) -> int:
    return subprocess.run(comando, check=False).returncode


def _validar_workflows_yaml(repo_root: Path) -> int:
    try:
        import yaml
    except ImportError:
        LOGGER.info("PyYAML no disponible, saltando yaml validation")
        return 0

    workflows = sorted((repo_root / ".github" / "workflows").glob("*.yml"))
    for workflow in workflows:
        with workflow.open("r", encoding="utf-8") as stream:
            try:
                yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                relativo = workflow.relative_to(repo_root)
                LOGGER.error("YAML inválido: %s (%s)", relativo, exc)
                return 1
    return 0


def main() -> int:
    repo_root = Path(resolver_repo_root())
    os.chdir(repo_root)

    rc_lint = _ejecutar_comando([sys.executable, "-m", "scripts.lint_py"])
    rc_estructura = _ejecutar_comando([sys.executable, "-m", "scripts.structural_gate"])
    rc_yaml = _validar_workflows_yaml(repo_root)

    if rc_lint != 0:
        return rc_lint
    if rc_estructura != 0:
        return rc_estructura
    return rc_yaml


if __name__ == "__main__":
    raise SystemExit(main())
