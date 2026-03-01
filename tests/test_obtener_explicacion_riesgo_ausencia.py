from __future__ import annotations

from dataclasses import dataclass

from clinicdesk.app.application.prediccion_ausencias.usecases import ObtenerExplicacionRiesgoAusenciaCita
from clinicdesk.app.domain.prediccion_ausencias import NivelRiesgo, PrediccionAusencia
from clinicdesk.app.infrastructure.prediccion_ausencias import MetadataModeloPrediccion, ModeloPrediccionNoDisponibleError
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries


@dataclass
class _FakePredictorEntrenado:
    nivel: NivelRiesgo = NivelRiesgo.MEDIO

    def predecir(self, citas):
        return [PrediccionAusencia(cita_id=citas[0].cita_id, riesgo=self.nivel, explicacion_corta="")]


class _FakeAlmacenamiento:
    def __init__(self, predictor=None, fail=False) -> None:
        self._predictor = predictor
        self._fail = fail

    def cargar(self):
        if self._fail:
            raise ModeloPrediccionNoDisponibleError()
        metadata = MetadataModeloPrediccion(
            fecha_entrenamiento="2026-01-02T10:00:00+00:00",
            citas_usadas=120,
            version="v1",
        )
        return self._predictor, metadata


def _insertar_cita(db_connection, *, paciente_id: int, medico_id: int, sala_id: int, inicio: str, estado: str) -> int:
    cursor = db_connection.execute(
        """
        INSERT INTO citas (paciente_id, medico_id, sala_id, inicio, fin, estado, motivo, notas, activo)
        VALUES (?, ?, ?, ?, ?, ?, '', '', 1)
        """,
        (paciente_id, medico_id, sala_id, inicio, "2026-01-10 11:00:00", estado),
    )
    db_connection.commit()
    return int(cursor.lastrowid)


def test_obtener_explicacion_con_predictor_historial_devuelve_motivos(container, seed_data) -> None:
    cita_id = _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2026-01-10 10:00:00",
        estado="PROGRAMADA",
    )
    _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2025-12-01 10:00:00",
        estado="NO_PRESENTADO",
    )

    uc = ObtenerExplicacionRiesgoAusenciaCita(
        queries=PrediccionAusenciasQueries(container.connection),
        almacenamiento=_FakeAlmacenamiento(_FakePredictorEntrenado(NivelRiesgo.ALTO)),
    )

    resultado = uc.ejecutar(cita_id)

    assert resultado.nivel == "ALTO"
    assert resultado.motivos
    assert any(item.code == "HISTORIAL_AUSENCIAS" for item in resultado.motivos)


def test_obtener_explicacion_sin_predictor_devuelve_no_disponible(container, seed_data) -> None:
    cita_id = _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_activo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2026-01-20 09:00:00",
        estado="PROGRAMADA",
    )
    uc = ObtenerExplicacionRiesgoAusenciaCita(
        queries=PrediccionAusenciasQueries(container.connection),
        almacenamiento=_FakeAlmacenamiento(fail=True),
    )

    resultado = uc.ejecutar(cita_id)

    assert resultado.nivel == "NO_DISPONIBLE"
    assert resultado.metadata_simple.necesita_entrenar is True
    assert resultado.motivos[0].code == "PREDICCION_NO_DISPONIBLE"


def test_obtener_explicacion_con_pocos_datos_incluye_motivo(container, seed_data) -> None:
    cita_id = _insertar_cita(
        container.connection,
        paciente_id=seed_data["paciente_inactivo_id"],
        medico_id=seed_data["medico_activo_id"],
        sala_id=seed_data["sala_activa_id"],
        inicio="2026-01-03 09:00:00",
        estado="PROGRAMADA",
    )

    uc = ObtenerExplicacionRiesgoAusenciaCita(
        queries=PrediccionAusenciasQueries(container.connection),
        almacenamiento=_FakeAlmacenamiento(_FakePredictorEntrenado(NivelRiesgo.MEDIO)),
    )

    resultado = uc.ejecutar(cita_id)

    assert any(item.code == "POCOS_DATOS_PACIENTE" for item in resultado.motivos)
