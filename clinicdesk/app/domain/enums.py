# domain/enums.py
from __future__ import annotations
from enum import Enum


class TipoDocumento(str, Enum):
    DNI = "DNI"
    NIE = "NIE"
    PASAPORTE = "PASAPORTE"
    OTRO = "OTRO"


class TipoSala(str, Enum):
    CONSULTA = "CONSULTA"
    FISIOTERAPIA = "FISIOTERAPIA"
    RX = "RX"
    ANALISIS = "ANALISIS"
    QUIROFANO = "QUIROFANO"
    OTRO = "OTRO"


class EstadoCita(str, Enum):
    PROGRAMADA = "PROGRAMADA"
    CONFIRMADA = "CONFIRMADA"
    EN_CURSO = "EN_CURSO"
    REALIZADA = "REALIZADA"
    CANCELADA = "CANCELADA"
    NO_PRESENTADO = "NO_PRESENTADO"


class TipoMovimientoStock(str, Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"


# -------------------------
# Incidencias (auditoría)
# -------------------------

class SeveridadIncidencia(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class EstadoIncidencia(str, Enum):
    ABIERTA = "ABIERTA"
    EN_REVISION = "EN_REVISION"
    RESUELTA = "RESUELTA"
    DESCARTADA = "DESCARTADA"


class TipoIncidencia(str, Enum):
    # Agenda / cuadrantes
    CITA_SIN_CUADRANTE = "CITA_SIN_CUADRANTE"
    CITA_FUERA_TURNO = "CITA_FUERA_TURNO"

    # Dispensación / stock
    DISPENSACION_SIN_CUADRANTE = "DISPENSACION_SIN_CUADRANTE"
    DISPENSACION_FUERA_TURNO = "DISPENSACION_FUERA_TURNO"
