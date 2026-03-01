from clinicdesk.app.ui.vistas.main_window.validacion_preventiva import (
    parse_and_validate_iso_date,
    validate_tramo_with_inputs,
)


def test_parse_and_validate_iso_date_accepts_valid_iso_date():
    assert parse_and_validate_iso_date("2026-12-31") is True


def test_parse_and_validate_iso_date_rejects_invalid_values():
    assert parse_and_validate_iso_date("31-12-2026") is False
    assert parse_and_validate_iso_date("2026-02-30") is False


def test_validate_tramo_with_inputs_uses_validator_output():
    def fake_validator(fecha: str, tramo: str):
        if fecha == "2026-01-01" and tramo == "manana":
            return (None, None)
        return ("fecha", "tramo")

    assert validate_tramo_with_inputs(
        validate_request_inputs=fake_validator,
        fecha="2026-01-01",
        tramo="manana",
    ) == (None, None)

    assert validate_tramo_with_inputs(
        validate_request_inputs=fake_validator,
        fecha="2026-01-02",
        tramo="tarde",
    ) == ("fecha", "tramo")
