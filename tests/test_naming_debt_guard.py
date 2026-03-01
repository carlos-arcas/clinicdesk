from pathlib import Path


ALLOWED_DEBT_FILES = {
    "clinicdesk/app/ui/vistas/main_window/validacion_preventiva.py",
}


def test_naming_debt_guard_baseline_is_explicit_for_new_files():
    missing = [path for path in ALLOWED_DEBT_FILES if not Path(path).exists()]
    assert not missing, f"Actualiza baseline: archivos faltantes {missing}"
