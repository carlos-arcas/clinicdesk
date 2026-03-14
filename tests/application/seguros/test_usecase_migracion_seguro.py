from clinicdesk.app.application.seguros import (
    AnalizarMigracionSeguroUseCase,
    CatalogoPlanesSeguro,
    SolicitudAnalisisMigracionSeguro,
)


def test_usecase_entrega_resumen_ejecutivo() -> None:
    use_case = AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro())

    respuesta = use_case.execute(
        SolicitudAnalisisMigracionSeguro(
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
            edad=34,
            residencia_pais="ES",
            historial_impagos=False,
            preexistencias_graves=False,
        )
    )

    assert "mejoras=" in respuesta.simulacion.resumen_ejecutivo
    assert respuesta.comparacion.coincidencias
