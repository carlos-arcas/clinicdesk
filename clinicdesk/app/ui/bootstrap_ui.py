from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Iterable, Sequence

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pages_registry import PageRegistry

LOGGER = get_logger(__name__)
_MAX_ERROR_LEN = 120


@dataclass(frozen=True)
class _PageEntry:
    key: str
    title: str
    factory: Callable[[], object]


@dataclass(frozen=True)
class RegistroPaginaSpec:
    page_id: str
    modulo_registro: str
    requiere_i18n: bool = False


@dataclass(frozen=True)
class ResultadoReintentoPagina:
    ok: bool
    mensaje: str = ""
    pagina_recuperada: object | None = None


class _FactoryPaginaRecargable:
    def __init__(self, factory_inicial: Callable[[], object]) -> None:
        self._factory_actual = factory_inicial

    def crear(self) -> object:
        return self._factory_actual()

    def actualizar(self, nueva_factory: Callable[[], object]) -> None:
        self._factory_actual = nueva_factory


def _build_specs_por_defecto() -> tuple[RegistroPaginaSpec, ...]:
    return (
        RegistroPaginaSpec("home", "clinicdesk.app.pages.home.register", requiere_i18n=True),
        RegistroPaginaSpec("pacientes", "clinicdesk.app.pages.pacientes.register"),
        RegistroPaginaSpec("citas", "clinicdesk.app.pages.citas.register", requiere_i18n=True),
        RegistroPaginaSpec("confirmaciones", "clinicdesk.app.pages.confirmaciones.register", requiere_i18n=True),
        RegistroPaginaSpec("medicos", "clinicdesk.app.pages.medicos.register"),
        RegistroPaginaSpec("personal", "clinicdesk.app.pages.personal.register"),
        RegistroPaginaSpec("salas", "clinicdesk.app.pages.salas.register"),
        RegistroPaginaSpec("farmacia", "clinicdesk.app.pages.farmacia.register"),
        RegistroPaginaSpec("medicamentos", "clinicdesk.app.pages.medicamentos.register"),
        RegistroPaginaSpec("materiales", "clinicdesk.app.pages.materiales.register"),
        RegistroPaginaSpec("recetas", "clinicdesk.app.pages.recetas.register"),
        RegistroPaginaSpec("dispensaciones", "clinicdesk.app.pages.dispensaciones.register"),
        RegistroPaginaSpec("turnos", "clinicdesk.app.pages.turnos.register"),
        RegistroPaginaSpec("ausencias", "clinicdesk.app.pages.ausencias.register"),
        RegistroPaginaSpec("incidencias", "clinicdesk.app.pages.incidencias.register"),
        RegistroPaginaSpec("auditoria", "clinicdesk.app.pages.auditoria.register"),
        RegistroPaginaSpec(
            "prediccion_ausencias", "clinicdesk.app.pages.prediccion_ausencias.register", requiere_i18n=True
        ),
        RegistroPaginaSpec(
            "prediccion_operativa", "clinicdesk.app.pages.prediccion_operativa.register", requiere_i18n=True
        ),
        RegistroPaginaSpec("gestion", "clinicdesk.app.pages.gestion.register", requiere_i18n=True),
        RegistroPaginaSpec("seguros", "clinicdesk.app.pages.seguros.register", requiere_i18n=True),
    )


def _truncar_error(error: Exception) -> str:
    return str(error).strip().replace("\n", " ")[:_MAX_ERROR_LEN]


def _crear_placeholder_page_def(
    *,
    i18n: I18nManager,
    page_id: str,
    codigo_error: str,
    detalles_cortos: str,
    factory_recargable: _FactoryPaginaRecargable,
    recargar_callback: Callable[[], ResultadoReintentoPagina],
):
    def _factory():
        from clinicdesk.app.pages.placeholder.page_no_disponible import PageNoDisponible

        return PageNoDisponible(
            i18n=i18n,
            nombre_pagina=page_id,
            codigo_error=codigo_error,
            detalles_cortos=detalles_cortos,
            on_reintentar=recargar_callback,
        )

    factory_recargable.actualizar(_factory)
    return _PageEntry(
        key=page_id,
        title=page_id,
        factory=factory_recargable.crear,
    )


def _cargar_registrador(spec: RegistroPaginaSpec) -> Callable[..., None]:
    modulo = import_module(spec.modulo_registro)
    return modulo.register


def _invocar_registrador(
    *,
    registrador: Callable[..., None],
    spec: RegistroPaginaSpec,
    registry: PageRegistry,
    container,
    i18n: I18nManager,
) -> None:
    if spec.requiere_i18n:
        registrador(registry, container, i18n)
        return
    registrador(registry, container)


def _resolver_pagina_recuperada(
    *,
    spec: RegistroPaginaSpec,
    container,
    i18n: I18nManager,
) -> _PageEntry:
    registrador = _cargar_registrador(spec)
    registry_temporal = PageRegistry()
    _invocar_registrador(
        registrador=registrador,
        spec=spec,
        registry=registry_temporal,
        container=container,
        i18n=i18n,
    )
    return registry_temporal.get(spec.page_id)


def _registrar_placeholder(
    *,
    registry: PageRegistry,
    container,
    i18n: I18nManager,
    spec: RegistroPaginaSpec,
    codigo_error: str,
    detalles_cortos: str,
) -> None:
    factory_recargable = _FactoryPaginaRecargable(lambda: None)

    def _reintentar() -> ResultadoReintentoPagina:
        try:
            pagina_recuperada = _resolver_pagina_recuperada(spec=spec, container=container, i18n=i18n)
        except Exception as exc:  # pragma: no cover - defensivo
            return ResultadoReintentoPagina(ok=False, mensaje=_truncar_error(exc))
        factory_recargable.actualizar(pagina_recuperada.factory)
        return ResultadoReintentoPagina(ok=True, pagina_recuperada=pagina_recuperada.factory())

    registry.register(
        _crear_placeholder_page_def(
            i18n=i18n,
            page_id=spec.page_id,
            codigo_error=codigo_error,
            detalles_cortos=detalles_cortos,
            factory_recargable=factory_recargable,
            recargar_callback=_reintentar,
        )
    )


def _log_page_error(*, spec: RegistroPaginaSpec, reason_code: str, error: Exception) -> None:
    LOGGER.error(
        "page_register_fail",
        extra={
            "action": "page_register_fail",
            "page": spec.page_id,
            "reason_code": reason_code,
            "exc_type": type(error).__name__,
            "exc_message": _truncar_error(error),
        },
    )


def _registrar_paginas_seguras(
    *,
    specs: Iterable[RegistroPaginaSpec],
    registry: PageRegistry,
    container,
    i18n: I18nManager,
) -> None:
    for spec in specs:
        try:
            registrador = _cargar_registrador(spec)
        except Exception as error:
            _log_page_error(spec=spec, reason_code="import_error", error=error)
            _registrar_placeholder(
                registry=registry,
                container=container,
                i18n=i18n,
                spec=spec,
                codigo_error="import_error",
                detalles_cortos=_truncar_error(error),
            )
            continue

        try:
            _invocar_registrador(
                registrador=registrador,
                spec=spec,
                registry=registry,
                container=container,
                i18n=i18n,
            )
        except Exception as error:
            _log_page_error(spec=spec, reason_code="register_error", error=error)
            _registrar_placeholder(
                registry=registry,
                container=container,
                i18n=i18n,
                spec=spec,
                codigo_error="register_error",
                detalles_cortos=_truncar_error(error),
            )


def get_pages(
    container,
    i18n: I18nManager,
    specs_paginas: Sequence[RegistroPaginaSpec] | None = None,
):
    registry = PageRegistry()
    specs = specs_paginas or _build_specs_por_defecto()
    _registrar_paginas_seguras(specs=specs, registry=registry, container=container, i18n=i18n)
    return registry.list()
