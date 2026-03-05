from __future__ import annotations

from datetime import date

import pytest

from clinicdesk.app.application.usecases.dashboard_gestion import (
    FiltrosDashboardDTO,
    ObtenerDashboardGestion,
    UMBRAL_ALERTA_ESPERA_ALTA_MIN,
    UMBRAL_ALERTA_POCOS_DATOS_ESPERA,
    UMBRAL_ALERTA_RETRASO_ALTO_MIN,
    normalizar_filtros_dashboard,
)
from clinicdesk.app.application.usecases.dashboard_gestion_prediccion import CitaGestionHoyDTO
from clinicdesk.app.application.usecases.obtener_metricas_operativas import (
    KpiDiaDTO,
    KpiMedicoDTO,
    ResultadoMetricasOperativasDTO,
)
from clinicdesk.app.domain.exceptions import ValidationError


class _FakeMetricas:
    def __init__(self, resultado: ResultadoMetricasOperativasDTO) -> None:
        self._resultado = resultado
        self.last_desde: date | None = None
        self.last_hasta: date | None = None

    def execute(self, desde: date, hasta: date) -> ResultadoMetricasOperativasDTO:
        self.last_desde = desde
        self.last_hasta = hasta
        return self._resultado


class _FakeAusencias:
    def __init__(self, salud: str = "VERDE", riesgos: dict[int, str] | None = None) -> None:
        self._salud = salud
        self._riesgos = riesgos or {}
        self.llamadas_riesgo = 0

    def obtener_salud(self) -> str:
        return self._salud

    def obtener_riesgo(self, citas: tuple) -> dict[int, str]:
        self.llamadas_riesgo += 1
        return {cita.id: self._riesgos.get(cita.id, "BAJO") for cita in citas}


class _FakeOperativa:
    def __init__(
        self,
        salud_duracion: str = "VERDE",
        salud_espera: str = "VERDE",
        duraciones: dict[int, str] | None = None,
        esperas: dict[int, str] | None = None,
    ) -> None:
        self._salud_duracion = salud_duracion
        self._salud_espera = salud_espera
        self._duraciones = duraciones or {}
        self._esperas = esperas or {}
        self.llamadas_estimaciones = 0

    def obtener_salud_duracion(self) -> str:
        return self._salud_duracion

    def obtener_salud_espera(self) -> str:
        return self._salud_espera

    def obtener_estimaciones_agenda(self) -> tuple[dict[int, str], dict[int, str]]:
        self.llamadas_estimaciones += 1
        return self._duraciones, self._esperas


class _FakeCitasHoy:
    def __init__(self, citas: tuple[CitaGestionHoyDTO, ...]) -> None:
        self._citas = citas
        self.llamadas = 0

    def listar_citas_hoy_gestion(self, limite: int) -> tuple[CitaGestionHoyDTO, ...]:
        self.llamadas += 1
        return self._citas[:limite]


def test_normalizar_filtros_dashboard_aplica_preset_7_dias() -> None:
    resultado = normalizar_filtros_dashboard(FiltrosDashboardDTO(preset="bad"), date(2025, 1, 31))

    assert resultado.preset == "7_DIAS"
    assert resultado.desde == date(2025, 1, 25)
    assert resultado.hasta == date(2025, 1, 31)


def test_normalizar_filtros_dashboard_personalizado_ordenado() -> None:
    resultado = normalizar_filtros_dashboard(
        FiltrosDashboardDTO(preset="PERSONALIZADO", desde=date(2025, 2, 5), hasta=date(2025, 2, 1)),
        date(2025, 2, 10),
    )

    assert resultado.desde == date(2025, 2, 1)
    assert resultado.hasta == date(2025, 2, 5)


def test_normalizar_filtros_dashboard_valida_rango_maximo() -> None:
    with pytest.raises(ValidationError):
        normalizar_filtros_dashboard(
            FiltrosDashboardDTO(preset="PERSONALIZADO", desde=date(2025, 1, 1), hasta=date(2025, 4, 5)),
            date(2025, 4, 5),
        )


def test_use_case_dashboard_deriva_top_alertas_y_vigilancia() -> None:
    fake_metricas = _FakeMetricas(_resultado_metricas(espera=20.0, retraso=12.0, total_validas_espera=10))
    fake_ausencias = _FakeAusencias(salud="AMARILLO", riesgos={1: "ALTO", 2: "BAJO", 3: "ALTO"})
    fake_operativa = _FakeOperativa(
        salud_duracion="VERDE",
        salud_espera="ROJO",
        duraciones={1: "ALTO", 2: "ALTO"},
        esperas={3: "ALTO"},
    )
    fake_citas = _FakeCitasHoy(
        (
            _cita(1, "08:30:00"),
            _cita(2, "08:15:00"),
            _cita(3, "08:00:00"),
            _cita(4, "07:45:00"),
        )
    )
    use_case = ObtenerDashboardGestion(fake_metricas, fake_ausencias, fake_operativa, fake_citas)

    resultado = use_case.execute(FiltrosDashboardDTO(preset="HOY"), hoy=date(2025, 1, 10))

    assert fake_metricas.last_desde == date(2025, 1, 10)
    assert resultado.kpis_resumen.total_citas == 15
    assert len(resultado.top_medicos) == 5
    assert resultado.top_medicos[0].medico_nombre == "Medico C"
    assert resultado.estados_prediccion.salud_ausencias.estado == "AMARILLO"
    assert resultado.estados_prediccion.salud_espera.estado == "ROJO"
    assert [x.cita_id for x in resultado.citas_a_vigilar] == [3, 1, 2]


def test_scoring_prioriza_dos_senales_sobre_una() -> None:
    use_case = ObtenerDashboardGestion(
        _FakeMetricas(_resultado_metricas(espera=8.0, retraso=1.0, total_validas_espera=100)),
        _FakeAusencias(riesgos={11: "ALTO", 12: "BAJO"}),
        _FakeOperativa(duraciones={11: "ALTO", 12: "ALTO"}, esperas={}),
        _FakeCitasHoy((_cita(11, "10:00:00"), _cita(12, "09:00:00"), _cita(13, "08:00:00"))),
    )

    resultado = use_case.execute(FiltrosDashboardDTO())

    assert [x.cita_id for x in resultado.citas_a_vigilar] == [11, 12]


def test_consultas_batch_sin_llamadas_por_fila() -> None:
    fake_metricas = _FakeMetricas(_resultado_metricas(espera=8.0, retraso=1.0, total_validas_espera=100))
    fake_ausencias = _FakeAusencias(riesgos={1: "ALTO", 2: "ALTO"})
    fake_operativa = _FakeOperativa(duraciones={1: "ALTO", 2: "ALTO"}, esperas={1: "ALTO"})
    fake_citas = _FakeCitasHoy((_cita(1, "09:00:00"), _cita(2, "10:00:00")))
    use_case = ObtenerDashboardGestion(fake_metricas, fake_ausencias, fake_operativa, fake_citas)

    use_case.execute(FiltrosDashboardDTO())

    assert fake_citas.llamadas == 1
    assert fake_ausencias.llamadas_riesgo == 1
    assert fake_operativa.llamadas_estimaciones == 1


def test_alertas_respetan_umbrales_estrictos() -> None:
    fake = _FakeMetricas(
        _resultado_metricas(
            espera=UMBRAL_ALERTA_ESPERA_ALTA_MIN,
            retraso=UMBRAL_ALERTA_RETRASO_ALTO_MIN,
            total_validas_espera=UMBRAL_ALERTA_POCOS_DATOS_ESPERA,
        )
    )
    use_case = ObtenerDashboardGestion(fake, _FakeAusencias(), _FakeOperativa(), _FakeCitasHoy(tuple()))

    resultado = use_case.execute(FiltrosDashboardDTO(preset="HOY"), hoy=date(2025, 1, 10))

    assert resultado.alertas == ()


def _resultado_metricas(espera: float, retraso: float, total_validas_espera: int) -> ResultadoMetricasOperativasDTO:
    por_dia = (
        KpiDiaDTO(
            fecha="2025-01-10",
            total_citas=15,
            total_validas_espera=total_validas_espera,
            espera_media_min=espera,
            total_validas_consulta=10,
            consulta_media_min=25.0,
            total_clinica_media_min=40.0,
            total_validas_retraso=8,
            retraso_media_min=retraso,
            descartados=0,
        ),
    )
    por_medico = (
        KpiMedicoDTO(1, "Medico A", 3, 8.0, 20.0, 2.0),
        KpiMedicoDTO(2, "Medico B", 2, 7.0, 18.0, 1.0),
        KpiMedicoDTO(3, "Medico C", 5, 10.0, 22.0, 3.0),
        KpiMedicoDTO(4, "Medico D", 1, 6.0, 17.0, 0.5),
        KpiMedicoDTO(5, "Medico E", 2, 6.5, 16.0, 0.5),
        KpiMedicoDTO(6, "Medico F", 2, 7.5, 19.0, 1.5),
    )
    return ResultadoMetricasOperativasDTO(
        desde="2025-01-10", hasta="2025-01-10", por_dia=por_dia, por_medico=por_medico
    )


def _cita(cita_id: int, hora: str) -> CitaGestionHoyDTO:
    return CitaGestionHoyDTO(
        cita_id=cita_id,
        hora=hora,
        paciente_nombre=f"Paciente {cita_id}",
        medico_nombre=f"Medico {cita_id}",
        paciente_id=100 + cita_id,
        medico_id=200 + cita_id,
        antelacion_dias=1,
    )
