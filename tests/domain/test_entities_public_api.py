"""Contrato público del módulo de compatibilidad de entidades."""

from importlib import import_module


def test_entities_all_exporta_simbolos_existentes() -> None:
    modulo = import_module("clinicdesk.app.domain.entities")
    simbolos = getattr(modulo, "__all__")
    for simbolo in simbolos:
        assert hasattr(modulo, simbolo)


def test_entities_all_sin_duplicados() -> None:
    modulo = import_module("clinicdesk.app.domain.entities")
    simbolos = getattr(modulo, "__all__")
    assert len(simbolos) == len(set(simbolos))
