"""CLI simple para exponer la versión de ClinicDesk."""

from clinicdesk import __version__


def main() -> None:
    """Imprime la versión actual del paquete."""
    print(__version__)


if __name__ == "__main__":
    main()
