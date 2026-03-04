"""CLI simple para exponer la versión de ClinicDesk."""

import logging
import sys

from clinicdesk import __version__


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
