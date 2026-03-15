from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Protocol

from clinicdesk.app.application.seguros.analitica_ejecutiva import CampaniaAccionableSeguro
from clinicdesk.app.domain.seguros import (
    CampaniaSeguro,
    CriterioCampaniaSeguro,
    EstadoCampaniaSeguro,
    EstadoItemCampaniaSeguro,
    ItemCampaniaSeguro,
    OrigenCampaniaSeguro,
    ResultadoItemCampaniaSeguro,
    crear_resultado_vacio,
    nuevo_item_campania,
    reconstruir_resultado,
)


class RepositorioCampaniaSeguro(Protocol):
    def crear_campania(self, campania: CampaniaSeguro, items: tuple[ItemCampaniaSeguro, ...]) -> None: ...

    def guardar_campania(self, campania: CampaniaSeguro) -> None: ...

    def obtener_campania(self, id_campania: str) -> CampaniaSeguro: ...

    def listar_campanias(self) -> tuple[CampaniaSeguro, ...]: ...

    def listar_items_campania(self, id_campania: str) -> tuple[ItemCampaniaSeguro, ...]: ...

    def guardar_item_campania(self, item: ItemCampaniaSeguro) -> None: ...


@dataclass(frozen=True, slots=True)
class SolicitudCrearCampaniaSeguro:
    id_campania: str
    nombre: str
    objetivo_comercial: str
    criterio: CriterioCampaniaSeguro
    ids_oportunidad: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SolicitudCrearCampaniaDesdeSugerencia:
    id_campania_nueva: str
    objetivo_comercial: str
    sugerencia: CampaniaAccionableSeguro


@dataclass(frozen=True, slots=True)
class SolicitudGestionItemCampaniaSeguro:
    id_campania: str
    id_item: str
    estado_trabajo: EstadoItemCampaniaSeguro
    accion_tomada: str
    resultado: ResultadoItemCampaniaSeguro
    nota_corta: str


class GestionCampaniasSeguroService:
    def __init__(self, repositorio: RepositorioCampaniaSeguro) -> None:
        self._repositorio = repositorio

    def crear_campania(self, solicitud: SolicitudCrearCampaniaSeguro) -> CampaniaSeguro:
        items = tuple(
            nuevo_item_campania(solicitud.id_campania, id_oportunidad, posicion)
            for posicion, id_oportunidad in enumerate(solicitud.ids_oportunidad, start=1)
        )
        campania = CampaniaSeguro(
            id_campania=solicitud.id_campania,
            nombre=solicitud.nombre,
            objetivo_comercial=solicitud.objetivo_comercial,
            creado_en=datetime.now(tz=UTC),
            criterio=solicitud.criterio,
            tamano_lote=len(items),
            estado=EstadoCampaniaSeguro.CREADA,
            resultado_agregado=crear_resultado_vacio(len(items)),
        )
        self._repositorio.crear_campania(campania, items)
        return campania

    def crear_desde_sugerencia(self, solicitud: SolicitudCrearCampaniaDesdeSugerencia) -> CampaniaSeguro:
        criterio = CriterioCampaniaSeguro(
            origen=OrigenCampaniaSeguro.SUGERENCIA,
            descripcion=solicitud.sugerencia.criterio,
            id_referencia=solicitud.sugerencia.id_campania,
        )
        return self.crear_campania(
            SolicitudCrearCampaniaSeguro(
                id_campania=solicitud.id_campania_nueva,
                nombre=solicitud.sugerencia.titulo,
                objetivo_comercial=solicitud.objetivo_comercial,
                criterio=criterio,
                ids_oportunidad=solicitud.sugerencia.ids_oportunidad,
            )
        )

    def listar_campanias(self) -> tuple[CampaniaSeguro, ...]:
        return self._repositorio.listar_campanias()

    def obtener_detalle(self, id_campania: str) -> tuple[CampaniaSeguro, tuple[ItemCampaniaSeguro, ...]]:
        campania = self._repositorio.obtener_campania(id_campania)
        items = self._repositorio.listar_items_campania(id_campania)
        return campania, items

    def registrar_resultado_item(self, solicitud: SolicitudGestionItemCampaniaSeguro) -> CampaniaSeguro:
        campania = self._repositorio.obtener_campania(solicitud.id_campania)
        item = self._buscar_item(solicitud.id_campania, solicitud.id_item)
        actualizado = replace(
            item,
            estado_trabajo=solicitud.estado_trabajo,
            accion_tomada=solicitud.accion_tomada or "-",
            resultado=solicitud.resultado,
            nota_corta=solicitud.nota_corta or "-",
            timestamp=datetime.now(tz=UTC),
        )
        self._repositorio.guardar_item_campania(actualizado)
        items = self._repositorio.listar_items_campania(solicitud.id_campania)
        resultado = reconstruir_resultado(items)
        if campania.estado is EstadoCampaniaSeguro.CREADA:
            campania = campania.iniciar()
        campania = replace(campania, resultado_agregado=resultado)
        if resultado.pendientes == 0:
            campania = campania.cerrar(resultado)
        self._repositorio.guardar_campania(campania)
        return campania

    def _buscar_item(self, id_campania: str, id_item: str) -> ItemCampaniaSeguro:
        for item in self._repositorio.listar_items_campania(id_campania):
            if item.id_item == id_item:
                return item
        raise KeyError(id_item)
