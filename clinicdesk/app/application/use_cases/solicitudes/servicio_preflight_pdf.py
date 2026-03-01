from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata

from clinicdesk.app.application.ports.sistema_archivos_puerto import SistemaArchivosPuerto

_MAX_INTENTOS_SUGERENCIA = 20


@dataclass(frozen=True, slots=True)
class EntradaNombrePdf:
    solicitud_id: str
    paciente_nombre: str
    fecha_referencia: str | None = None


@dataclass(frozen=True, slots=True)
class ResultadoPreflightPdf:
    ruta_destino: str
    colision: bool
    ruta_sugerida: str | None
    motivos: tuple[str, ...]


@dataclass(slots=True)
class ServicioPreflightPdf:
    sistema_archivos: SistemaArchivosPuerto

    def preflight(self, entrada: EntradaNombrePdf, carpeta_destino: str | Path) -> ResultadoPreflightPdf:
        ruta_destino = self.construir_ruta_destino(entrada, carpeta_destino)
        return self.validar_colision(ruta_destino)

    def construir_nombre_pdf(self, entrada: EntradaNombrePdf) -> str:
        partes = ["solicitud", entrada.solicitud_id, entrada.paciente_nombre]
        if entrada.fecha_referencia:
            partes.append(entrada.fecha_referencia)
        base = _normalizar_nombre("_".join(partes))
        return f"{base}.pdf"

    def construir_ruta_destino(self, entrada: EntradaNombrePdf, carpeta_destino: str | Path) -> str:
        carpeta = Path(carpeta_destino)
        return str(carpeta / self.construir_nombre_pdf(entrada))

    def validar_colision(self, ruta: str) -> ResultadoPreflightPdf:
        if not self.sistema_archivos.existe_ruta(ruta):
            return ResultadoPreflightPdf(
                ruta_destino=ruta,
                colision=False,
                ruta_sugerida=None,
                motivos=("ruta_disponible",),
            )
        sugerida = self._sugerir_ruta_alternativa(ruta)
        motivos = ("ruta_existente", "sugerencia_encontrada")
        if sugerida is None:
            motivos = ("ruta_existente", "sin_sugerencia_disponible")
        return ResultadoPreflightPdf(
            ruta_destino=ruta,
            colision=True,
            ruta_sugerida=sugerida,
            motivos=motivos,
        )

    def _sugerir_ruta_alternativa(self, ruta_original: str) -> str | None:
        ruta = Path(ruta_original)
        for indice in range(1, _MAX_INTENTOS_SUGERENCIA + 1):
            candidata = str(ruta.with_name(f"{ruta.stem} ({indice}){ruta.suffix}"))
            if not self.sistema_archivos.existe_ruta(candidata):
                return candidata
        return None


def _normalizar_nombre(texto: str) -> str:
    texto_ascii = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto_limpio = re.sub(r"[^\w\-]+", "_", texto_ascii, flags=re.ASCII)
    texto_limpio = re.sub(r"_+", "_", texto_limpio).strip("_-")
    return texto_limpio or "documento"
