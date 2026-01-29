from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List

from clinicdesk.app.domain.modelos import Paciente, Cita, Medico
from clinicdesk.app.domain.repositorios import RepositorioPacientes, RepositorioCitas,RepositorioMedicos
# Importamos contratos del dominio: esta capa IMPLEMENTA esos contratos usando SQLite.


class RepositorioPacientesSQLite(RepositorioPacientes):
    """
    Implementación SQLite del repositorio de pacientes.

    Recibe sqlite3.Connection:
      - Se usa para ejecutar SQL y obtener filas.
    """

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def listar_todos(self) -> List[Paciente]:
        filas = self.conexion.execute(
            "SELECT id, nombre, telefono FROM pacientes ORDER BY id DESC"
        ).fetchall()

        # Gracias a haber usado row_factory en la creacion de la conexion se permite el uso de fila["id"] etc en lugar de fila[0],fila[1]...
        return [
            Paciente(
                id=int(f["id"]),
                nombre=str(f["nombre"]),
                telefono=str(f["telefono"]),
            )
            for f in filas
        ]

    def crear(self, nombre: str, telefono: str) -> int:
        cur = self.conexion.execute(
            "INSERT INTO pacientes (nombre, telefono) VALUES (?, ?)",
            (nombre, telefono or ""),
        )
        self.conexion.commit()
        return int(cur.lastrowid)


class RepositorioMedicosSQLite(RepositorioMedicos):
    """
    Implementación SQLite del repositorio de pacientes.

    Recibe sqlite3.Connection:
      - Se usa para ejecutar SQL y obtener filas.
    """

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def listar_todos(self) -> List[Paciente]:
        filas = self.conexion.execute(
            "SELECT id, nombre, telefono FROM pacientes ORDER BY id DESC"
        ).fetchall()

        # Gracias a haber usado row_factory en la creacion de la conexion se permite el uso de fila["id"] etc en lugar de fila[0],fila[1]...
        return [
            Paciente(
                id=int(f["id"]),
                nombre=str(f["nombre"]),
                telefono=str(f["telefono"]),
            )
            for f in filas
        ]

    def crear(self, nombre: str, telefono: str) -> int:
        cur = self.conexion.execute(
            "INSERT INTO pacientes (nombre, telefono) VALUES (?, ?)",
            (nombre, telefono or ""),
        )
        self.conexion.commit()
        return int(cur.lastrowid)



class RepositorioCitasSQLite(RepositorioCitas):
    """Implementación SQLite del repositorio de citas."""

    def __init__(self, conexion: sqlite3.Connection) -> None:
        self.conexion = conexion

    def listar_todas(self) -> List[Cita]:
        filas = self.conexion.execute(
            "SELECT id, id_paciente, fecha_hora, motivo FROM citas ORDER BY fecha_hora DESC"
        ).fetchall()

        return [
            Cita(
                id=int(f["id"]),
                id_paciente=int(f["id_paciente"]),
                # Guardamos datetime como ISO string en DB, lo recuperamos y parseamos:
                fecha_hora=datetime.fromisoformat(str(f["fecha_hora"])),
                motivo=str(f["motivo"]),
            )
            for f in filas
        ]

    def crear(self, id_paciente: int, fecha_hora: datetime, motivo: str) -> int:
        cur = self.conexion.execute(
            "INSERT INTO citas (id_paciente, fecha_hora, motivo) VALUES (?, ?, ?)",
            (id_paciente, fecha_hora.isoformat(timespec="minutes"), motivo),
        )
        self.conexion.commit()
        return int(cur.lastrowid)
