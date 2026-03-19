from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Callable, Iterable, Sequence

from clinicdesk.app.bootstrap_logging import get_logger
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pages_registry import PageRegistry

LOGGER = get_logger(__name__)
_MAX_ERROR_LEN = 120


@dataclass
class _PageEntry:
    key: str
    title: str
    factory: Callable[[], object]


@dataclass(frozen=True)
class RegistroPaginaSpec:
    page_id: str
    modulo_registro: str
    requiere_i18n: bool = False
    titulo: str | None = None
    titulo_key_i18n: str | None = None


@dataclass(frozen=True)
class ResultadoReintentoPagina:
    ok: bool
    mensaje: str = ""
    pagina_recuperada: object | None = None
    page_id: str = ""
    titulo_pagina: str = ""


class _FactoryPaginaRecargable:
    def __init__(self, factory_inicial: Callable[[], object]) -> None:
        self._factory_actual = factory_inicial

    def crear(self) -> object:
        return self._factory_actual()

    def actualizar(self, nueva_factory: Callable[[], object]) -> None:
        self._factory_actual = nueva_factory


def _build_specs_por_defecto() -> tuple[RegistroPaginaSpec, ...]:
    return (
        RegistroPaginaSpec(
            "home", "clinicdesk.app.pages.home.register", requiere_i18n=True, titulo_key_i18n="nav.home"
        ),
        RegistroPaginaSpec("pacientes", "clinicdesk.app.pages.pacientes.register", titulo="Pacientes"),
        RegistroPaginaSpec("citas", "clinicdesk.app.pages.citas.register", requiere_i18n=True, titulo="Citas"),
        RegistroPaginaSpec(
            "confirmaciones",
            "clinicdesk.app.pages.confirmaciones.register",
            requiere_i18n=True,
            titulo_key_i18n="nav.confirmaciones",
        ),
        RegistroPaginaSpec("medicos", "clinicdesk.app.pages.medicos.register", titulo="Médicos"),
        RegistroPaginaSpec("personal", "clinicdesk.app.pages.personal.register", titulo="Personal"),
        RegistroPaginaSpec("salas", "clinicdesk.app.pages.salas.register", titulo="Salas"),
        RegistroPaginaSpec("farmacia", "clinicdesk.app.pages.farmacia.register", titulo="Farmacia"),
        RegistroPaginaSpec("medicamentos", "clinicdesk.app.pages.medicamentos.register", titulo="Medicamentos"),
        RegistroPaginaSpec("materiales", "clinicdesk.app.pages.materiales.register", titulo="Materiales"),
        RegistroPaginaSpec("recetas", "clinicdesk.app.pages.recetas.register", titulo="Recetas"),
        RegistroPaginaSpec("dispensaciones", "clinicdesk.app.pages.dispensaciones.register", titulo="Dispensaciones"),
        RegistroPaginaSpec("turnos", "clinicdesk.app.pages.turnos.register", titulo="Turnos / Cuadrantes"),
        RegistroPaginaSpec("ausencias", "clinicdesk.app.pages.ausencias.register", titulo="Ausencias"),
        RegistroPaginaSpec("incidencias", "clinicdesk.app.pages.incidencias.register", titulo="Incidencias"),
        RegistroPaginaSpec("auditoria", "clinicdesk.app.pages.auditoria.register", titulo="Auditoría"),
        RegistroPaginaSpec(
            "prediccion_ausencias",
            "clinicdesk.app.pages.prediccion_ausencias.register",
            requiere_i18n=True,
            titulo_key_i18n="nav.prediccion_ausencias",
        ),
        RegistroPaginaSpec(
            "prediccion_operativa",
            "clinicdesk.app.pages.prediccion_operativa.register",
            requiere_i18n=True,
            titulo_key_i18n="nav.prediccion_operativa",
        ),
        RegistroPaginaSpec(
            "gestion", "clinicdesk.app.pages.gestion.register", requiere_i18n=True, titulo_key_i18n="nav.gestion"
        ),
        RegistroPaginaSpec(
            "seguros", "clinicdesk.app.pages.seguros.register", requiere_i18n=True, titulo_key_i18n="nav.seguros"
        ),
    )


def _truncar_error(error: Exception) -> str:
    return str(error).strip().replace("\n", " ")[:_MAX_ERROR_LEN]


def _resolver_titulo_placeholder(spec: RegistroPaginaSpec, i18n: I18nManager) -> str:
    if spec.titulo_key_i18n:
        return i18n.t(spec.titulo_key_i18n)
    if spec.titulo:
        return spec.titulo
    return spec.page_id


def _crear_placeholder_page_def(
    *,
    i18n: I18nManager,
    page_id: str,
    titulo_visible: str,
    codigo_error: str,
    detalles_cortos: str,
    factory_recargable: _FactoryPaginaRecargable,
    recargar_callback: Callable[[], ResultadoReintentoPagina],
):
    def _factory():
        from clinicdesk.app.pages.placeholder.page_no_disponible import PageNoDisponible

        return PageNoDisponible(
            i18n=i18n,
            nombre_pagina=titulo_visible,
            codigo_error=codigo_error,
            detalles_cortos=detalles_cortos,
            on_reintentar=recargar_callback,
        )

    factory_recargable.actualizar(_factory)
    return _PageEntry(
        key=page_id,
        title=titulo_visible,
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
    titulo_placeholder = _resolver_titulo_placeholder(spec, i18n)
    page_entry: _PageEntry

    def _reintentar() -> ResultadoReintentoPagina:
        try:
            pagina_recuperada = _resolver_pagina_recuperada(spec=spec, container=container, i18n=i18n)
        except Exception as exc:  # pragma: no cover - defensivo
            return ResultadoReintentoPagina(ok=False, mensaje=_truncar_error(exc))
        page_entry.title = pagina_recuperada.title
        factory_recargable.actualizar(pagina_recuperada.factory)
        return ResultadoReintentoPagina(
            ok=True,
            pagina_recuperada=pagina_recuperada.factory(),
            page_id=pagina_recuperada.key,
            titulo_pagina=pagina_recuperada.title,
        )

    page_entry = _crear_placeholder_page_def(
        i18n=i18n,
        page_id=spec.page_id,
        titulo_visible=titulo_placeholder,
        codigo_error=codigo_error,
        detalles_cortos=detalles_cortos,
        factory_recargable=factory_recargable,
        recargar_callback=_reintentar,
    )
    registry.register(page_entry)


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
