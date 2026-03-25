from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clinicdesk.app.application.prediccion_ausencias.usecases import (
    ComprobarDatosPrediccionAusencias,
    EntrenamientoPrediccionError,
    EntrenarPrediccionAusencias,
    PrevisualizarPrediccionAusencias,
    _evaluar_predictor,
    _split_determinista_train_validacion,
)
from clinicdesk.app.domain.prediccion_ausencias import RegistroEntrenamiento
from clinicdesk.app.infrastructure.prediccion_ausencias import (
    AlmacenamientoModeloPrediccion,
    PredictorAusenciasBaseline,
)
from clinicdesk.app.queries.prediccion_ausencias_queries import PrediccionAusenciasQueries


def _seed_base_tablas(con) -> tuple[int, int, int]:
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '1', 'Ana', 'Uno', 1)"
    )
    con.execute(
        "INSERT INTO pacientes(tipo_documento, documento, nombre, apellidos, activo) VALUES ('DNI', '2', 'Beto', 'Dos', 1)"
    )
    con.execute(
        "INSERT INTO medicos(tipo_documento, documento, nombre, apellidos, activo, num_colegiado, especialidad) VALUES ('DNI', '11', 'Med', 'Uno', 1, 'C1', 'General')"
    )
    con.execute("INSERT INTO salas(nombre, tipo, activa) VALUES ('S1', 'CONSULTA', 1)")
    con.commit()
    return 1, 1, 1


def _insert_cita(con, *, paciente_id: int, medico_id: int, sala_id: int, inicio: datetime, estado: str) -> None:
    fin = inicio + timedelta(minutes=30)
    con.execute(
        """
        INSERT INTO citas(paciente_id, medico_id, sala_id, inicio, fin, estado, activo)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (paciente_id, medico_id, sala_id, inicio.isoformat(), fin.isoformat(), estado),
    )


def test_comprobar_datos_prediccion_detecta_minimo(db_connection) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    queries = PrediccionAusenciasQueries(db_connection)
    uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=3)

    for day in range(2):
        _insert_cita(
            db_connection,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.now() - timedelta(days=30 - day),
            estado="REALIZADA",
        )
    db_connection.commit()

    resultado = uc.ejecutar()
    assert resultado.citas_validas == 2
    assert resultado.apto_para_entrenar is False
    assert resultado.mensaje_clave == "prediccion_ausencias.estado.datos_insuficientes"


def test_entrenar_guarda_modelo_actualiza_metadata_y_recarga_predice(db_connection, tmp_path: Path) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for idx in range(60):
        estado = "NO_PRESENTADO" if idx % 3 == 0 else "REALIZADA"
        _insert_cita(
            db_connection,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.now() - timedelta(days=90 - idx),
            estado=estado,
        )
    db_connection.commit()

    queries = PrediccionAusenciasQueries(db_connection)
    almacenamiento = AlmacenamientoModeloPrediccion(tmp_path)
    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(comprobar_uc, queries, PredictorAusenciasBaseline(), almacenamiento)

    resultado = entrenar_uc.ejecutar()
    predictor, metadata = almacenamiento.cargar()
    predicciones = predictor.predecir([])
    metadata_path = almacenamiento.carpeta_modelo / "metadata.json"
    metadata_json = json.loads(metadata_path.read_text(encoding="utf-8"))

    assert resultado.citas_usadas == 60
    assert metadata.citas_usadas == 60
    assert metadata.model_type == "PredictorAusenciasBaseline"
    assert metadata.muestras_train == 48
    assert metadata.muestras_validacion == 12
    assert metadata.accuracy is not None
    assert metadata.precision_no_show is not None
    assert metadata.recall_no_show is not None
    assert metadata.f1_no_show is not None
    assert metadata_json["citas_usadas"] == 60
    assert metadata_json["muestras_train"] == 48
    assert metadata_json["muestras_validacion"] == 12
    assert datetime.fromisoformat(metadata_json["fecha_entrenamiento"])
    assert predicciones == []


def test_entrenar_sin_datos_lanza_error_funcional_tipado(db_connection, tmp_path: Path) -> None:
    _, _, _ = _seed_base_tablas(db_connection)
    queries = PrediccionAusenciasQueries(db_connection)
    almacenamiento = AlmacenamientoModeloPrediccion(tmp_path)
    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(comprobar_uc, queries, PredictorAusenciasBaseline(), almacenamiento)

    with pytest.raises(EntrenamientoPrediccionError) as exc_info:
        entrenar_uc.ejecutar()

    assert exc_info.value.reason_code == "dataset_insuficiente"


def test_entrenar_io_error_lanza_reason_code_save_failed(db_connection, tmp_path: Path) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    for idx in range(60):
        _insert_cita(
            db_connection,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.now() - timedelta(days=100 - idx),
            estado="REALIZADA",
        )
    db_connection.commit()

    queries = PrediccionAusenciasQueries(db_connection)
    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(
        comprobar_uc, queries, PredictorAusenciasBaseline(), _AlmacenamientoQueFalla()
    )

    with pytest.raises(EntrenamientoPrediccionError) as exc_info:
        entrenar_uc.ejecutar()

    assert exc_info.value.reason_code == "save_failed"


def test_previsualizar_sin_y_con_modelo(db_connection, tmp_path: Path) -> None:
    paciente_id, medico_id, sala_id = _seed_base_tablas(db_connection)
    queries = PrediccionAusenciasQueries(db_connection)
    almacenamiento = AlmacenamientoModeloPrediccion(tmp_path)
    previsualizar = PrevisualizarPrediccionAusencias(queries, almacenamiento)

    sin_modelo = previsualizar.ejecutar(limite=5)
    assert sin_modelo.estado == "SIN_MODELO"

    for idx in range(55):
        estado = "NO_PRESENTADO" if idx % 2 == 0 else "REALIZADA"
        _insert_cita(
            db_connection,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.now() - timedelta(days=120 - idx),
            estado=estado,
        )

    for idx in range(3):
        _insert_cita(
            db_connection,
            paciente_id=paciente_id,
            medico_id=medico_id,
            sala_id=sala_id,
            inicio=datetime.now() + timedelta(days=idx + 1),
            estado="PROGRAMADA",
        )
    db_connection.commit()

    comprobar_uc = ComprobarDatosPrediccionAusencias(queries, minimo_requerido=50)
    entrenar_uc = EntrenarPrediccionAusencias(comprobar_uc, queries, PredictorAusenciasBaseline(), almacenamiento)
    entrenar_uc.ejecutar()

    con_modelo = previsualizar.ejecutar(limite=5)
    assert con_modelo.estado == "LISTO"
    assert len(con_modelo.items) == 3
    assert {item.riesgo for item in con_modelo.items}.issubset({"BAJO", "MEDIO", "ALTO"})


class _AlmacenamientoQueFalla:
    def guardar(self, predictor_entrenado, *, citas_usadas: int, version: str, **kwargs):  # noqa: ARG002
        raise OSError("disk_full")


def test_split_determinista_separa_train_y_validacion_en_orden_temporal() -> None:
    dataset = [
        RegistroEntrenamiento(paciente_id=1, no_vino=0, dias_antelacion=3),
        RegistroEntrenamiento(paciente_id=2, no_vino=1, dias_antelacion=4),
        RegistroEntrenamiento(paciente_id=3, no_vino=0, dias_antelacion=5),
        RegistroEntrenamiento(paciente_id=4, no_vino=1, dias_antelacion=6),
        RegistroEntrenamiento(paciente_id=5, no_vino=0, dias_antelacion=7),
    ]

    train, validacion = _split_determinista_train_validacion(dataset, proporcion_validacion=0.4)

    assert train == dataset[:3]
    assert validacion == dataset[3:]


def test_evaluacion_predictor_es_determinista_y_sin_nan(db_connection, tmp_path: Path) -> None:
    dataset_train = [RegistroEntrenamiento(paciente_id=1, no_vino=0, dias_antelacion=10)] * 3
    dataset_validacion = [
        RegistroEntrenamiento(paciente_id=1, no_vino=0, dias_antelacion=9),
        RegistroEntrenamiento(paciente_id=1, no_vino=1, dias_antelacion=1),
    ]
    predictor = PredictorAusenciasBaseline().entrenar(dataset_train)

    evaluacion = _evaluar_predictor(
        predictor_entrenado=predictor,
        dataset_train=dataset_train,
        dataset_validacion=dataset_validacion,
    )

    assert evaluacion.muestras_train == 3
    assert evaluacion.muestras_validacion == 2
    assert 0.0 <= evaluacion.accuracy <= 1.0
    assert 0.0 <= evaluacion.precision_no_show <= 1.0
    assert 0.0 <= evaluacion.recall_no_show <= 1.0
    assert 0.0 <= evaluacion.f1_no_show <= 1.0


def test_cargar_metadata_antigua_mantiene_compatibilidad(tmp_path: Path) -> None:
    almacenamiento = AlmacenamientoModeloPrediccion(tmp_path)
    metadata_path = almacenamiento.carpeta_modelo / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(
            {
                "fecha_entrenamiento": "2026-03-20T12:00:00+00:00",
                "citas_usadas": 50,
                "version": "prediccion_ausencias_v1",
            }
        ),
        encoding="utf-8",
    )

    metadata = almacenamiento.cargar_metadata()

    assert metadata is not None
    assert metadata.citas_usadas == 50
    assert metadata.model_type == "PredictorAusenciasBaseline"
    assert metadata.accuracy is None
