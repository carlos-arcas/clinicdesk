import ast
from pathlib import Path


EXPECTED_METHODS = {
    "_bind_preventive_validation_events",
    "_mark_field_touched",
    "_schedule_preventive_validation",
    "_run_preventive_validation",
    "_collect_base_preventive_errors",
    "_collect_preventive_validation",
    "_collect_preventive_business_rules",
    "_collect_pending_duplicates_warning",
    "_on_go_to_existing_duplicate",
    "_render_preventive_validation",
    "_run_preconfirm_checks",
}


def test_main_window_has_preventive_validation_wrappers():
    source = Path("clinicdesk/app/ui/main_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    class_node = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "MainWindow"
    )
    method_names = {node.name for node in class_node.body if isinstance(node, ast.FunctionDef)}

    missing = EXPECTED_METHODS - method_names
    assert not missing, f"Faltan wrappers en MainWindow: {sorted(missing)}"
