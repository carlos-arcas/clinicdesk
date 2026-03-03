from clinicdesk.app.ui.navigation_intent_store import IntentConsumible


def test_intent_se_consume_una_vez_y_se_limpia() -> None:
    store = IntentConsumible[int]()
    store.guardar(42)

    assert store.consumir() == 42
    assert store.consumir() is None
