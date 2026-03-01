from __future__ import annotations

from clinicdesk.app.domain.citas_privacidad import NivelSensibilidadCita, nivel_sensibilidad_atributo_cita
from clinicdesk.app.domain.pacientes_mascaras import enmascarar_texto_general
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.queries.citas_queries import CitaRow


class FormateadorPrivacidadCitas:
    """Centraliza el formato de citas para vistas de listado/tooltip."""

    def formatear_valor(self, atributo: str, valor: str | None) -> str:
        texto = (valor or "").strip()
        if nivel_sensibilidad_atributo_cita(atributo) is NivelSensibilidadCita.PUBLICO:
            return texto
        return enmascarar_texto_general(texto)

    def construir_tooltip_calendario(self, cita: CitaRow, i18n: I18nManager, riesgo: str) -> str:
        riesgo_linea = i18n.t("citas.riesgo.tooltip").format(nivel=riesgo)
        notas_linea = self._linea_notas(cita.notas_len, i18n)
        return "\n".join([riesgo_linea, notas_linea])

    @staticmethod
    def _linea_notas(notas_len: int, i18n: I18nManager) -> str:
        if notas_len <= 0:
            return i18n.t("citas.tooltip.notas.sin")
        return i18n.t("citas.tooltip.notas.con").format(total=notas_len)
