from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.domain.seguros import (
    EstadoElegibilidadSeguro,
    PerfilCandidatoSeguro,
    PlanSeguro,
    ResultadoElegibilidadSeguro,
)


@dataclass(frozen=True, slots=True)
class DiferenciaCategoriaSeguro:
    categoria: str
    codigo: str
    origen: str
    destino: str
    impacto: str
    requiere_revision: bool = False


@dataclass(frozen=True, slots=True)
class ResultadoComparacionSeguro:
    coincidencias: tuple[DiferenciaCategoriaSeguro, ...]
    mejoras: tuple[DiferenciaCategoriaSeguro, ...]
    perdidas: tuple[DiferenciaCategoriaSeguro, ...]
    riesgos_migracion: tuple[str, ...]
    revision_humana: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResultadoSimulacionMigracionSeguro:
    clasificacion: str
    resumen_ejecutivo: str
    impactos_positivos: tuple[str, ...]
    impactos_negativos: tuple[str, ...]
    advertencias: tuple[str, ...]


def evaluar_elegibilidad(
    plan_destino: PlanSeguro,
    perfil: PerfilCandidatoSeguro,
) -> ResultadoElegibilidadSeguro:
    faltantes: list[str] = []
    razones: list[str] = []
    bloqueante = False
    requiere_revision = False
    for regla in plan_destino.reglas_elegibilidad:
        valor = getattr(perfil, regla.campo)
        if valor is None:
            faltantes.append(regla.campo)
            continue
        cumple = str(valor) == regla.valor_requerido
        if cumple:
            continue
        razones.append(regla.motivo)
        if regla.obligatoria:
            bloqueante = True
        else:
            requiere_revision = True

    if faltantes:
        return ResultadoElegibilidadSeguro(
            estado=EstadoElegibilidadSeguro.INFORMACION_INSUFICIENTE,
            razones=tuple(razones),
            campos_faltantes=tuple(sorted(set(faltantes))),
        )
    if bloqueante:
        return ResultadoElegibilidadSeguro(
            estado=EstadoElegibilidadSeguro.NO_ELEGIBLE,
            razones=tuple(razones),
            campos_faltantes=(),
        )
    estado = EstadoElegibilidadSeguro.ELEGIBLE_CON_REVISION if requiere_revision else EstadoElegibilidadSeguro.ELEGIBLE
    return ResultadoElegibilidadSeguro(estado=estado, razones=tuple(razones), campos_faltantes=())


def comparar_planes(origen: PlanSeguro, destino: PlanSeguro) -> ResultadoComparacionSeguro:
    coincidencias: list[DiferenciaCategoriaSeguro] = []
    mejoras: list[DiferenciaCategoriaSeguro] = []
    perdidas: list[DiferenciaCategoriaSeguro] = []
    revision_humana: list[str] = []

    _comparar_coberturas(origen, destino, coincidencias, mejoras, perdidas)
    _comparar_carencias(origen, destino, coincidencias, mejoras, perdidas)
    _comparar_copagos(origen, destino, coincidencias, mejoras, perdidas)
    _comparar_limites(origen, destino, coincidencias, mejoras, perdidas)
    _comparar_exclusiones(origen, destino, mejoras, perdidas, revision_humana)

    riesgos = tuple(diff.codigo for diff in perdidas)
    return ResultadoComparacionSeguro(
        coincidencias=tuple(coincidencias),
        mejoras=tuple(mejoras),
        perdidas=tuple(perdidas),
        riesgos_migracion=riesgos,
        revision_humana=tuple(revision_humana),
    )


def simular_migracion(
    origen: PlanSeguro, destino: PlanSeguro, perfil: PerfilCandidatoSeguro
) -> ResultadoSimulacionMigracionSeguro:
    comparacion = comparar_planes(origen, destino)
    elegibilidad = evaluar_elegibilidad(destino, perfil)
    positivos = [f"{item.categoria}:{item.codigo}" for item in comparacion.mejoras]
    negativos = [f"{item.categoria}:{item.codigo}" for item in comparacion.perdidas]
    advertencias = list(comparacion.revision_humana)

    if elegibilidad.estado is EstadoElegibilidadSeguro.NO_ELEGIBLE:
        clasificacion = "DESFAVORABLE"
        advertencias.extend(elegibilidad.razones)
    elif elegibilidad.estado is EstadoElegibilidadSeguro.INFORMACION_INSUFICIENTE:
        clasificacion = "REVISAR"
        advertencias.append("seguros.migracion.info_insuficiente")
    elif negativos and len(negativos) >= len(positivos):
        clasificacion = "DESFAVORABLE"
    elif advertencias or elegibilidad.estado is EstadoElegibilidadSeguro.ELEGIBLE_CON_REVISION:
        clasificacion = "REVISAR"
    else:
        clasificacion = "FAVORABLE"

    resumen = _construir_resumen(clasificacion, comparacion, elegibilidad)
    return ResultadoSimulacionMigracionSeguro(
        clasificacion=clasificacion,
        resumen_ejecutivo=resumen,
        impactos_positivos=tuple(positivos),
        impactos_negativos=tuple(negativos),
        advertencias=tuple(advertencias),
    )


def _construir_resumen(
    clasificacion: str,
    comparacion: ResultadoComparacionSeguro,
    elegibilidad: ResultadoElegibilidadSeguro,
) -> str:
    return (
        f"{clasificacion}|"
        f"mejoras={len(comparacion.mejoras)}|"
        f"perdidas={len(comparacion.perdidas)}|"
        f"revision={len(comparacion.revision_humana)}|"
        f"elegibilidad={elegibilidad.estado.value}"
    )


def _comparar_coberturas(origen: PlanSeguro, destino: PlanSeguro, coincidencias, mejoras, perdidas) -> None:
    origen_map = {item.codigo: item for item in origen.coberturas}
    for destino_item in destino.coberturas:
        base = origen_map.get(destino_item.codigo)
        if base is None:
            mejoras.append(DiferenciaCategoriaSeguro("cobertura", destino_item.codigo, "N/A", "incluida", "MEJORA"))
            continue
        if base.incluida == destino_item.incluida:
            coincidencias.append(
                DiferenciaCategoriaSeguro(
                    "cobertura", destino_item.codigo, str(base.incluida), str(destino_item.incluida), "IGUAL"
                )
            )
            continue
        bucket = mejoras if destino_item.incluida else perdidas
        impacto = "MEJORA" if destino_item.incluida else "PERDIDA"
        bucket.append(
            DiferenciaCategoriaSeguro(
                "cobertura", destino_item.codigo, str(base.incluida), str(destino_item.incluida), impacto
            )
        )


def _comparar_carencias(origen: PlanSeguro, destino: PlanSeguro, coincidencias, mejoras, perdidas) -> None:
    base_map = {item.codigo: item.meses for item in origen.carencias}
    for item in destino.carencias:
        origen_meses = base_map.get(item.codigo, 0)
        if item.meses == origen_meses:
            coincidencias.append(
                DiferenciaCategoriaSeguro("carencia", item.codigo, str(origen_meses), str(item.meses), "IGUAL")
            )
        elif item.meses < origen_meses:
            mejoras.append(
                DiferenciaCategoriaSeguro("carencia", item.codigo, str(origen_meses), str(item.meses), "MEJORA")
            )
        else:
            perdidas.append(
                DiferenciaCategoriaSeguro("carencia", item.codigo, str(origen_meses), str(item.meses), "PERDIDA")
            )


def _comparar_copagos(origen: PlanSeguro, destino: PlanSeguro, coincidencias, mejoras, perdidas) -> None:
    base_map = {item.codigo: item.importe_fijo for item in origen.copagos}
    for item in destino.copagos:
        origen_importe = base_map.get(item.codigo, 0.0)
        if item.importe_fijo == origen_importe:
            coincidencias.append(
                DiferenciaCategoriaSeguro(
                    "copago", item.codigo, f"{origen_importe:.2f}", f"{item.importe_fijo:.2f}", "IGUAL"
                )
            )
        elif item.importe_fijo < origen_importe:
            mejoras.append(
                DiferenciaCategoriaSeguro(
                    "copago", item.codigo, f"{origen_importe:.2f}", f"{item.importe_fijo:.2f}", "MEJORA"
                )
            )
        else:
            perdidas.append(
                DiferenciaCategoriaSeguro(
                    "copago", item.codigo, f"{origen_importe:.2f}", f"{item.importe_fijo:.2f}", "PERDIDA"
                )
            )


def _comparar_limites(origen: PlanSeguro, destino: PlanSeguro, coincidencias, mejoras, perdidas) -> None:
    base_map = {item.codigo: item.maximo_anual for item in origen.limites}
    for item in destino.limites:
        limite_origen = base_map.get(item.codigo, 0)
        if item.maximo_anual == limite_origen:
            coincidencias.append(
                DiferenciaCategoriaSeguro("limite", item.codigo, str(limite_origen), str(item.maximo_anual), "IGUAL")
            )
        elif item.maximo_anual > limite_origen:
            mejoras.append(
                DiferenciaCategoriaSeguro("limite", item.codigo, str(limite_origen), str(item.maximo_anual), "MEJORA")
            )
        else:
            perdidas.append(
                DiferenciaCategoriaSeguro("limite", item.codigo, str(limite_origen), str(item.maximo_anual), "PERDIDA")
            )


def _comparar_exclusiones(origen: PlanSeguro, destino: PlanSeguro, mejoras, perdidas, revision_humana) -> None:
    origen_codigos = {item.codigo for item in origen.exclusiones}
    destino_codigos = {item.codigo for item in destino.exclusiones}
    for codigo in sorted(origen_codigos - destino_codigos):
        mejoras.append(DiferenciaCategoriaSeguro("exclusion", codigo, "aplica", "no_aplica", "MEJORA", True))
    for codigo in sorted(destino_codigos - origen_codigos):
        perdidas.append(DiferenciaCategoriaSeguro("exclusion", codigo, "no_aplica", "aplica", "PERDIDA", True))
        revision_humana.append(f"exclusion:{codigo}")
