from clinicdesk.app.application.seguros.analisis_migracion import (
    comparar_planes,
    evaluar_elegibilidad,
    simular_migracion,
)
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.domain.seguros import EstadoElegibilidadSeguro, PerfilCandidatoSeguro


def test_comparador_detecta_mejoras_y_perdidas() -> None:
    catalogo = CatalogoPlanesSeguro()
    origen = catalogo.obtener_por_id("externo_plus")
    destino = catalogo.obtener_por_id("clinica_esencial")

    resultado = comparar_planes(origen, destino)

    assert resultado.perdidas
    assert any(item.categoria == "cobertura" for item in resultado.perdidas)
    assert any(item.categoria == "copago" for item in resultado.mejoras)


def test_elegibilidad_reporta_info_insuficiente() -> None:
    catalogo = CatalogoPlanesSeguro()
    destino = catalogo.obtener_por_id("clinica_integral")

    resultado = evaluar_elegibilidad(
        destino,
        PerfilCandidatoSeguro(edad=None, residencia_pais="ES", historial_impagos=False, preexistencias_graves=False),
    )

    assert resultado.estado is EstadoElegibilidadSeguro.INFORMACION_INSUFICIENTE
    assert "edad" in resultado.campos_faltantes


def test_simulacion_desfavorable_si_no_elegible() -> None:
    catalogo = CatalogoPlanesSeguro()
    origen = catalogo.obtener_por_id("externo_basico")
    destino = catalogo.obtener_por_id("clinica_integral")

    simulacion = simular_migracion(
        origen,
        destino,
        PerfilCandidatoSeguro(edad=80, residencia_pais="ES", historial_impagos=False, preexistencias_graves=False),
    )

    assert simulacion.clasificacion == "DESFAVORABLE"
    assert simulacion.advertencias
