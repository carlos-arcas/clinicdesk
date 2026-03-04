from __future__ import annotations

from pathlib import Path

from scripts.check_security_docs import check_security_docs


def _crear_docs(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "threat_model.md").write_text("# Threat model\n", encoding="utf-8")
    (docs_dir / "security_regression_checklist.md").write_text("# Checklist\n", encoding="utf-8")


def test_check_security_docs_pass_si_todos_los_archivos_existen(tmp_path: Path) -> None:
    _crear_docs(tmp_path)

    assert check_security_docs(repo_root=tmp_path) == 0


def test_check_security_docs_fail_si_falta_un_archivo(tmp_path: Path) -> None:
    _crear_docs(tmp_path)
    (tmp_path / "docs" / "security_regression_checklist.md").unlink()

    assert check_security_docs(repo_root=tmp_path) == 2
