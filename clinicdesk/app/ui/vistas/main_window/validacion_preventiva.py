from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable


@dataclass(frozen=True)
class PreventiveValidationResult:
    blocking: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def parse_and_validate_iso_date(raw_value: str) -> bool:
    """Return True when *raw_value* is a valid ISO date (YYYY-MM-DD)."""
    try:
        date.fromisoformat(raw_value)
    except ValueError:
        return False
    return len(raw_value) == 10


def validate_tramo_with_inputs(
    *,
    validate_request_inputs: Callable[[str, str], tuple[str | None, str | None]],
    fecha: str,
    tramo: str,
) -> tuple[str | None, str | None]:
    """Pure adapter around request input validation for unit tests without Qt."""
    return validate_request_inputs(fecha, tramo)


def _bind_preventive_validation_events(window: Any) -> None:
    if hasattr(window, "_preventive_validation_bound"):
        window._preventive_validation_bound = True


def _mark_field_touched(window: Any, field_name: str) -> None:
    touched = getattr(window, "_preventive_touched_fields", set())
    touched.add(field_name)
    window._preventive_touched_fields = touched


def _schedule_preventive_validation(window: Any) -> None:
    scheduler = getattr(window, "_schedule_once", None)
    if callable(scheduler):
        scheduler(window._run_preventive_validation)
        return
    _run_preventive_validation(window)


def _run_preventive_validation(window: Any) -> PreventiveValidationResult:
    result = _collect_preventive_validation(window)
    _render_preventive_validation(window, result)
    window._preventive_validation_result = result
    return result


def _collect_base_preventive_errors(window: Any) -> tuple[str, ...]:
    errors: list[str] = []
    fecha = getattr(window, "_fecha_solicitud", "")
    if fecha and not parse_and_validate_iso_date(fecha):
        errors.append("Fecha inválida (YYYY-MM-DD).")
    return tuple(errors)


def _collect_preventive_business_rules(window: Any) -> tuple[str, ...]:
    collector = getattr(window, "_collect_business_rule_warnings", None)
    if callable(collector):
        data = collector()
        return tuple(str(x) for x in data)
    return ()


def _collect_pending_duplicates_warning(window: Any) -> tuple[str, ...]:
    duplicates = getattr(window, "_pending_duplicates", ())
    if not duplicates:
        return ()
    return ("Existe una solicitud pendiente duplicada.",)


def _collect_preventive_validation(window: Any) -> PreventiveValidationResult:
    blocking = list(_collect_base_preventive_errors(window))
    warnings = list(_collect_preventive_business_rules(window))
    warnings.extend(_collect_pending_duplicates_warning(window))
    return PreventiveValidationResult(tuple(blocking), tuple(warnings))


def _on_go_to_existing_duplicate(window: Any) -> None:
    callback = getattr(window, "_open_existing_duplicate", None)
    if callable(callback):
        callback()


def _render_preventive_validation(window: Any, result: PreventiveValidationResult) -> None:
    renderer = getattr(window, "_render_preventive_banner", None)
    if callable(renderer):
        renderer(result)


def _run_preconfirm_checks(window: Any) -> bool:
    result = _run_preventive_validation(window)
    return not result.blocking
