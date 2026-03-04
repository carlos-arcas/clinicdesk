"""CLI simple para exponer la versión de ClinicDesk."""

import logging
import sys

from clinicdesk import __version__


def assert_tag_matches_version(tag: str, version: str) -> None:
    """Valida que un tag ``vX.Y.Z`` coincida con la versión ``X.Y.Z``."""
    if not tag.startswith("v"):
        raise ValueError("El tag debe iniciar con 'v'.")

    version_desde_tag = tag[1:]
    if version_desde_tag != version:
        raise ValueError(
            "El tag no coincide con la versión actual: "
            f"tag={tag!r} version={version!r}."
        )


def _obtener_logger() -> logging.Logger:
    logger = logging.getLogger("scripts.version")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def main() -> None:
    """Emite la versión actual del paquete."""
    _obtener_logger().info(__version__)


if __name__ == "__main__":
    main()
