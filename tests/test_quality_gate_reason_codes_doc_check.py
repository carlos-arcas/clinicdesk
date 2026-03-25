from __future__ import annotations

from scripts.quality_gate_components import entrypoint
from scripts.quality_gate_components.contrato_reason_codes_doc import ErrorContratoReasonCodesDoc


def test_run_docs_checks_falla_si_contrato_reason_codes_no_coincide(monkeypatch, caplog) -> None:
    monkeypatch.setattr(
        entrypoint.gate_pr,
        "validar_contrato_reason_codes_doc",
        lambda: (_ for _ in ()).throw(ErrorContratoReasonCodesDoc("boom")),
    )
    monkeypatch.setattr(entrypoint, "check_security_docs", lambda **_kwargs: 0)
    monkeypatch.setattr(entrypoint, "check_changelog", lambda **_kwargs: None)

    rc = entrypoint._run_docs_checks()

    assert rc == 2
    assert "Contrato documental reason_code inválido" in caplog.text


def test_run_docs_checks_ejecuta_flujo_habitual_si_contrato_ok(monkeypatch) -> None:
    llamadas: list[str] = []
    monkeypatch.setattr(entrypoint.gate_pr, "validar_contrato_reason_codes_doc", lambda: llamadas.append("contrato"))
    monkeypatch.setattr(entrypoint, "check_security_docs", lambda **_kwargs: llamadas.append("security") or 0)
    monkeypatch.setattr(entrypoint, "check_changelog", lambda **_kwargs: llamadas.append("changelog"))

    rc = entrypoint._run_docs_checks()

    assert rc == 0
    assert llamadas == ["contrato", "security", "changelog"]
