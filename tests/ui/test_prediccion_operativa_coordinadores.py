from clinicdesk.app.pages.prediccion_operativa.coordinadores import (
    CoordinadorContextoPrediccionOperativa,
    CoordinadorRunsEntrenamientoPrediccionOperativa,
)


def test_contexto_operativo_invalida_runs_al_cambiar_visibilidad() -> None:
    coordinador = CoordinadorContextoPrediccionOperativa()

    token_1 = coordinador.on_show()
    token_2 = coordinador.on_hide()

    assert token_1 == 1
    assert token_2 == 2
    assert coordinador.contexto_vigente(token_1) is False


def test_runs_entrenamiento_marca_obsoleto_al_invalidar() -> None:
    coordinador = CoordinadorRunsEntrenamientoPrediccionOperativa()

    run = coordinador.iniciar_run("duracion", token_contexto=5)
    coordinador.invalidar_todos()

    assert coordinador.run_vigente("duracion", run.token) is False
    assert coordinador.contexto_de_run("duracion") == 5


def test_runs_entrenamiento_conserva_vigencia_por_tipo() -> None:
    coordinador = CoordinadorRunsEntrenamientoPrediccionOperativa()

    run_duracion = coordinador.iniciar_run("duracion", token_contexto=1)
    run_espera = coordinador.iniciar_run("espera", token_contexto=1)
    coordinador.iniciar_run("duracion", token_contexto=2)

    assert coordinador.run_vigente("duracion", run_duracion.token) is False
    assert coordinador.run_vigente("espera", run_espera.token) is True
