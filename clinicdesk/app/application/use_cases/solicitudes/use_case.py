from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from clinicdesk.app.application.use_cases.solicitudes.servicio_preflight_pdf import (
    EntradaNombrePdf,
    ServicioPreflightPdf,
)
from clinicdesk.app.domain.exceptions import BusinessRuleError


@dataclass(slots=True)
class UseCaseSolicitudesPdf:
    servicio_preflight_pdf: ServicioPreflightPdf

    def preparar_ruta_destino(self, entrada: EntradaNombrePdf, carpeta_destino: str | Path) -> str:
        resultado = self.servicio_preflight_pdf.preflight(entrada, carpeta_destino)
        if not resultado.colision:
            return resultado.ruta_destino
        detalle = f"Colisión de ruta destino: {resultado.ruta_destino}"
        if resultado.ruta_sugerida:
            detalle = f"{detalle}. Sugerencia: {resultado.ruta_sugerida}"
        raise BusinessRuleError(detalle)
