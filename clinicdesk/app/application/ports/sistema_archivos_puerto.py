from __future__ import annotations

from typing import Protocol


class SistemaArchivosPuerto(Protocol):
    """Puerto mínimo para consultas de preflight sin IO de escritura."""

    def existe_ruta(self, ruta: str) -> bool:
        """Indica si la ruta ya existe en el filesystem."""
