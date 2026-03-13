from __future__ import annotations

from clinicdesk.app.infrastructure.sqlite.personal.search import search_filters


class _ProteccionStub:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def hash_for_lookup(self, field: str, value: str) -> str:
        return f"hash:{field}:{value}"


def test_search_filters_con_cifrado_omite_like_en_documento() -> None:
    clauses, params = search_filters(
        field_protection=_ProteccionStub(enabled=True),
        texto="ana",
        puesto="recepcion",
        tipo_documento="DNI",
        documento="1234A",
        activo=True,
    )

    assert "documento_hash = ?" in clauses
    assert "documento LIKE ? COLLATE NOCASE" not in clauses
    assert "hash:documento:1234A" in params


def test_search_filters_sin_cifrado_usa_like_documento() -> None:
    clauses, params = search_filters(
        field_protection=_ProteccionStub(enabled=False),
        texto=None,
        puesto=None,
        tipo_documento=None,
        documento="1234A",
        activo=None,
    )

    assert clauses == ["documento LIKE ? COLLATE NOCASE"]
    assert params == ["%1234A%"]
