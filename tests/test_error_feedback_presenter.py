from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_module():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "clinicdesk" / "app" / "ui" / "ux" / "error_feedback.py"
    spec = spec_from_file_location("test_error_feedback_module", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_presentar_error_recuperable_mapea_mensaje_y_detalle() -> None:
    module = _load_module()
    feedback = module.presentar_error_recuperable(RuntimeError("fallo tecnico"))
    assert feedback.titulo_key == "ux.error.generic_title"
    assert feedback.mensaje_key == "ux.error.retryable_message"
    assert feedback.detalle == "fallo tecnico"
