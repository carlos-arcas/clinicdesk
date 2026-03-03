from __future__ import annotations

from clinicdesk.app.application.prediccion_ausencias.preferencias_resultados_recientes import (
    VENTANA_RESULTADOS_POR_DEFECTO,
    deserializar_ventana_resultados_semanas,
    serializar_ventana_resultados_semanas,
)
from clinicdesk.app.application.prediccion_ausencias.resultados_recientes import (
    ObtenerResultadosRecientesPrediccionAusencias,
    ventana_semanas_a_dias,
)
from clinicdesk.app.queries.prediccion_ausencias_resultados_queries import (
    DiagnosticoResultadosRecientesRaw,
    ResultadoRecientePrediccion,
)


def test_ventana_semanas_a_dias_valores_permitidos() -> None:
    assert ventana_semanas_a_dias(4) == 28
    assert ventana_semanas_a_dias(8) == 56
    assert ventana_semanas_a_dias(12) == 84


def test_ventana_semanas_a_dias_valor_invalido_usa_fallback() -> None:
    assert ventana_semanas_a_dias(5) == 56


def test_persistencia_ventana_serializa_y_deserializa() -> None:
    valor = serializar_ventana_resultados_semanas(12)

    assert valor == "12"
    assert deserializar_ventana_resultados_semanas(valor) == 12


def test_persistencia_ventana_invalida_usa_fallback() -> None:
    assert serializar_ventana_resultados_semanas(99) == str(VENTANA_RESULTADOS_POR_DEFECTO)
    assert deserializar_ventana_resultados_semanas("99") == VENTANA_RESULTADOS_POR_DEFECTO


def test_uc_envia_ventana_dias_correcta_al_repositorio() -> None:
    repo = _RepositorioFakeResultadosRecientes()
    uc = ObtenerResultadosRecientesPrediccionAusencias(repo, umbral_minimo=1)

    uc.ejecutar(ventana_semanas=4)

    assert repo.ventana_dias_diagnostico == 28


class _RepositorioFakeResultadosRecientes:
    def __init__(self) -> None:
        self.ventana_dias_diagnostico: int | None = None

    def obtener_diagnostico_resultados_recientes(self, ventana_dias: int) -> DiagnosticoResultadosRecientesRaw:
        self.ventana_dias_diagnostico = ventana_dias
        return DiagnosticoResultadosRecientesRaw(
            total_citas_cerradas_en_ventana=0,
            total_predicciones_registradas_en_ventana=0,
            total_predicciones_con_resultado=0,
            version_objetivo=None,
        )

    def obtener_resultados_recientes_prediccion(self, ventana_dias: int = 60) -> ResultadoRecientePrediccion:
        return ResultadoRecientePrediccion(version_modelo_fecha_utc=None, filas=tuple())

    def registrar_predicciones_ausencias(self, modelo_fecha_utc: str, items: list) -> int:
        return 0
