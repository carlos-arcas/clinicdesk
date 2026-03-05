from __future__ import annotations

from scripts.quality_gate_components.secrets_scan_fallback import render_report, scan_repo


def test_scan_repo_detecta_patrones_y_redacta_secretos(tmp_path) -> None:
    private_key_file = tmp_path / "private.pem"
    private_key_file.write_text("-----BEGIN " + "RSA" + " PRIVA" + "TE KEY-----\nabc\n", encoding="utf-8")

    github_token = "gh" + "p_" + "A" * 24
    token_file = tmp_path / "tokens.env"
    token_file.write_text(f"GITHUB_TOKEN={github_token}\n", encoding="utf-8")

    clean_file = tmp_path / "README.md"
    clean_file.write_text("texto limpio\n", encoding="utf-8")

    hallazgos = scan_repo(tmp_path)

    reglas = {(item.ruta, item.regla) for item in hallazgos}
    assert ("private.pem", "private_key") in reglas
    assert ("tokens.env", "github_token") in reglas
    assert all(item.ruta != "README.md" for item in hallazgos)

    report = render_report(hallazgos)
    assert github_token not in report
    assert "[REDACTED]" in report
