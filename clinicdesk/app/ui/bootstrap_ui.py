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


def _build_specs_por_defecto() -> tuple[RegistroPaginaSpec, ...]:
    return (
        RegistroPaginaSpec("home", "clinicdesk.app.pages.home.register"),
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
        RegistroPaginaSpec("demo_ml", "clinicdesk.app.pages.demo_ml.register", requiere_i18n=True),
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
    recargar_callback: Callable[[], tuple[bool, str]],
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

    return _PageEntry(
        key=page_id,
        title=page_id,
        factory=_factory,
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


def _registrar_placeholder(
    *,
    registry: PageRegistry,
    i18n: I18nManager,
    spec: RegistroPaginaSpec,
    codigo_error: str,
    detalles_cortos: str,
) -> None:
    def _reintentar() -> tuple[bool, str]:
        try:
            _cargar_registrador(spec)
        except Exception as exc:  # pragma: no cover - defensivo
            return False, _truncar_error(exc)
        return True, ""

    registry.register(
        _crear_placeholder_page_def(
            i18n=i18n,
            page_id=spec.page_id,
            codigo_error=codigo_error,
            detalles_cortos=detalles_cortos,
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
