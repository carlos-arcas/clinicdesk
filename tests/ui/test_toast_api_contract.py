from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_toast_module():
    repo_root = Path(__file__).resolve().parents[2]
    toast_path = repo_root / "clinicdesk" / "app" / "ui" / "widgets" / "toast.py"
    spec = spec_from_file_location("test_toast_module", toast_path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_no_typeerror_calls(manager) -> None:
    success = manager.success(
        "Guardado",
        title="Éxito",
        action_label="Deshacer",
        action_callback=lambda: None,
    )
    error = manager.error(
        "Falló",
        title="Error",
        action_label="Reintentar",
        action_callback=lambda: None,
    )

    assert success["action_label"] == "Deshacer"
    assert callable(success["action_callback"])
    assert error["action_label"] == "Reintentar"
    assert callable(error["action_callback"])


def test_gestor_toasts_acepta_action_kwargs_sin_typeerror() -> None:
    toast_module = _load_toast_module()
    _assert_no_typeerror_calls(toast_module.GestorToasts())


def test_toast_manager_acepta_action_kwargs_sin_typeerror() -> None:
    toast_module = _load_toast_module()
    _assert_no_typeerror_calls(toast_module.ToastManager())
