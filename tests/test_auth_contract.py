from pathlib import Path

from clinicdesk.app.security.auth import is_demo_mode_allowed


def test_demo_mode_allowed_only_for_demo_or_data_paths(tmp_path: Path) -> None:
    data_db = Path("./data/clinicdesk.db").resolve()
    demo_db = (tmp_path / "clinicdesk_demo.db").resolve()
    prod_db = (tmp_path / "prod.db").resolve()

    assert is_demo_mode_allowed(data_db) is True
    assert is_demo_mode_allowed(demo_db) is True
    assert is_demo_mode_allowed(prod_db) is False
