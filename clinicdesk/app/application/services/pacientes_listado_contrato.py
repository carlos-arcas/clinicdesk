"""Contrato de atributos de paciente para listados futuros."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from clinicdesk.app.domain.pacientes_atributos import ATRIBUTOS_PACIENTE
from clinicdesk.app.domain.pacientes_mascaras import (
    enmascarar_documento,
    enmascarar_email,
    enmascarar_telefono,
    enmascarar_texto_general,
)
from clinicdesk.app.domain.pacientes_privacidad import NivelSensibilidad, nivel_sensibilidad_de_atributo


@dataclass(frozen=True, slots=True)
class AtributoListadoPaciente:
    nombre: str
    tipo: str
    clave_i18n: str
    sensibilidad: NivelSensibilidad


class ContratoListadoPacientesService:
    """Expone metadatos y formato en modo listado sin depender de UI."""

    def atributos_disponibles(self) -> tuple[AtributoListadoPaciente, ...]:
        return tuple(self._crear_descriptor(atributo.nombre, atributo.tipo) for atributo in ATRIBUTOS_PACIENTE)

    def formatear_valor_listado(self, atributo: str, valor: Any) -> str:
        texto = self._normalizar_a_texto(valor)
        sensibilidad = nivel_sensibilidad_de_atributo(atributo)
        if sensibilidad is NivelSensibilidad.PUBLICO:
            return texto
        return self._enmascarar_por_atributo(atributo, texto)

    @staticmethod
    def _crear_descriptor(nombre: str, tipo: str) -> AtributoListadoPaciente:
        return AtributoListadoPaciente(
            nombre=nombre,
            tipo=tipo,
            clave_i18n=f"pacientes.{nombre}",
            sensibilidad=nivel_sensibilidad_de_atributo(nombre),
        )

    @staticmethod
    def _normalizar_a_texto(valor: Any) -> str:
        if valor is None:
            return ""
        if isinstance(valor, bool):
            return "1" if valor else "0"
        return str(valor).strip()

    @staticmethod
    def _enmascarar_por_atributo(atributo: str, valor: str) -> str:
        mascaras = {
            "documento": enmascarar_documento,
            "telefono": enmascarar_telefono,
            "email": enmascarar_email,
        }
        funcion = mascaras.get(atributo, enmascarar_texto_general)
        return funcion(valor)
