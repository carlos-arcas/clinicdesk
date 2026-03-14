from __future__ import annotations

from clinicdesk.app.domain.seguros import (
    CarenciaSeguro,
    CoberturaSeguro,
    CopagoSeguro,
    ExclusionSeguro,
    LimiteSeguro,
    PlanSeguro,
    ReglaElegibilidadSeguro,
    TipoPlanSeguro,
)


class CatalogoPlanesSeguro:
    def __init__(self) -> None:
        self._planes = _planes_demo()

    def listar_planes(self) -> tuple[PlanSeguro, ...]:
        return self._planes

    def listar_planes_clinica(self) -> tuple[PlanSeguro, ...]:
        return tuple(plan for plan in self._planes if plan.tipo_plan is TipoPlanSeguro.CLINICA)

    def listar_planes_origen(self) -> tuple[PlanSeguro, ...]:
        return tuple(plan for plan in self._planes if plan.tipo_plan is TipoPlanSeguro.EXTERNO)

    def obtener_por_id(self, plan_id: str) -> PlanSeguro:
        for plan in self._planes:
            if plan.id_plan == plan_id:
                return plan
        raise ValueError(f"plan_no_encontrado:{plan_id}")


def _planes_demo() -> tuple[PlanSeguro, ...]:
    reglas_base = (
        ReglaElegibilidadSeguro("edad_max", "edad", "70", True, "seguros.elegibilidad.edad_maxima"),
        ReglaElegibilidadSeguro("residencia", "residencia_pais", "ES", True, "seguros.elegibilidad.residencia"),
        ReglaElegibilidadSeguro(
            "sin_impagos", "historial_impagos", "False", False, "seguros.elegibilidad.revision_impagos"
        ),
    )
    return (
        PlanSeguro(
            id_plan="externo_basico",
            nombre="Plan General Básico",
            tipo_plan=TipoPlanSeguro.EXTERNO,
            cuota_mensual=39.0,
            coberturas=(
                CoberturaSeguro("consulta_general", "Consulta general", True),
                CoberturaSeguro("urgencias", "Urgencias", True),
                CoberturaSeguro("hospitalizacion", "Hospitalización", False),
            ),
            carencias=(CarenciaSeguro("hospitalizacion", 10),),
            copagos=(CopagoSeguro("consulta_general", 14.0), CopagoSeguro("urgencias", 22.0)),
            limites=(LimiteSeguro("consulta_general", 8), LimiteSeguro("urgencias", 2)),
            exclusiones=(ExclusionSeguro("embarazo", "Cobertura de embarazo no incluida"),),
            reglas_elegibilidad=reglas_base,
        ),
        PlanSeguro(
            id_plan="externo_plus",
            nombre="Plan General Plus",
            tipo_plan=TipoPlanSeguro.EXTERNO,
            cuota_mensual=65.0,
            coberturas=(
                CoberturaSeguro("consulta_general", "Consulta general", True),
                CoberturaSeguro("urgencias", "Urgencias", True),
                CoberturaSeguro("hospitalizacion", "Hospitalización", True),
            ),
            carencias=(CarenciaSeguro("hospitalizacion", 6),),
            copagos=(CopagoSeguro("consulta_general", 9.0), CopagoSeguro("urgencias", 15.0)),
            limites=(LimiteSeguro("consulta_general", 20), LimiteSeguro("urgencias", 6)),
            exclusiones=(),
            reglas_elegibilidad=reglas_base,
        ),
        PlanSeguro(
            id_plan="clinica_esencial",
            nombre="Seguro Clínica Esencial",
            tipo_plan=TipoPlanSeguro.CLINICA,
            cuota_mensual=54.0,
            coberturas=(
                CoberturaSeguro("consulta_general", "Consulta general", True),
                CoberturaSeguro("urgencias", "Urgencias", True),
                CoberturaSeguro("hospitalizacion", "Hospitalización", False),
            ),
            carencias=(CarenciaSeguro("hospitalizacion", 8),),
            copagos=(CopagoSeguro("consulta_general", 7.0), CopagoSeguro("urgencias", 12.0)),
            limites=(LimiteSeguro("consulta_general", 30), LimiteSeguro("urgencias", 4)),
            exclusiones=(ExclusionSeguro("estetica", "No cubre cirugía estética"),),
            reglas_elegibilidad=reglas_base,
        ),
        PlanSeguro(
            id_plan="clinica_integral",
            nombre="Seguro Clínica Integral",
            tipo_plan=TipoPlanSeguro.CLINICA,
            cuota_mensual=79.0,
            coberturas=(
                CoberturaSeguro("consulta_general", "Consulta general", True),
                CoberturaSeguro("urgencias", "Urgencias", True),
                CoberturaSeguro("hospitalizacion", "Hospitalización", True),
            ),
            carencias=(CarenciaSeguro("hospitalizacion", 4),),
            copagos=(CopagoSeguro("consulta_general", 4.0), CopagoSeguro("urgencias", 8.0)),
            limites=(LimiteSeguro("consulta_general", 40), LimiteSeguro("urgencias", 12)),
            exclusiones=(),
            reglas_elegibilidad=reglas_base,
        ),
    )
