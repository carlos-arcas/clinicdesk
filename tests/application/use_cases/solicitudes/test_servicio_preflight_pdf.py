from __future__ import annotations

from clinicdesk.app.application.use_cases.solicitudes.servicio_preflight_pdf import (
    EntradaNombrePdf,
    ServicioPreflightPdf,
)


class FakeSistemaArchivos:
    def __init__(self, existentes: set[str] | None = None) -> None:
        self._existentes = existentes or set()

    def existe_ruta(self, ruta: str) -> bool:
        return ruta in self._existentes


def test_validar_colision_ok_si_ruta_no_existe() -> None:
    servicio = ServicioPreflightPdf(FakeSistemaArchivos())

    resultado = servicio.validar_colision("/tmp/solicitud_100.pdf")

    assert resultado.colision is False
    assert resultado.ruta_sugerida is None
    assert resultado.motivos == ("ruta_disponible",)


def test_validar_colision_propone_sugerencia_si_ya_existe() -> None:
    existentes = {
        "/tmp/solicitud_100.pdf",
        "/tmp/solicitud_100 (1).pdf",
    }
    servicio = ServicioPreflightPdf(FakeSistemaArchivos(existentes))

    resultado = servicio.validar_colision("/tmp/solicitud_100.pdf")

    assert resultado.colision is True
    assert resultado.ruta_sugerida == "/tmp/solicitud_100 (2).pdf"
    assert resultado.motivos == ("ruta_existente", "sugerencia_encontrada")


def test_construir_nombre_pdf_normaliza_caracteres_raros_de_forma_estable() -> None:
    servicio = ServicioPreflightPdf(FakeSistemaArchivos())
    entrada = EntradaNombrePdf(
        solicitud_id="Nº 45/7",
        paciente_nombre="Óscar / Núñez *Prueba*",
        fecha_referencia="2026-01-31 09:45",
    )

    nombre = servicio.construir_nombre_pdf(entrada)

    assert nombre == "solicitud_No_45_7_Oscar_Nunez_Prueba_2026-01-31_09_45.pdf"
