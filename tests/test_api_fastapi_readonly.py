from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from clinicdesk.web.api.app import create_app
from clinicdesk.web.api.servicio_consultas import ServicioConsultasApi


class _ServicioMock(ServicioConsultasApi):
    def __init__(self) -> None:
        pass

    def listar_citas(self, filtros):
        return [
            {
                "id": 1,
                "fecha": "2026-01-10",
                "hora_inicio": "09:00:00",
                "hora_fin": "09:15:00",
                "estado": "PENDIENTE",
                "sala": "SALA-1",
                "medico": "Dra. Casa",
                "paciente": "Ana López",
                "tiene_incidencias": 0,
            }
        ]

    def buscar_pacientes(self, texto: str):
        return [
            {
                "id": 7,
                "nombre": "Ana",
                "apellidos": "López",
                "nombre_completo": "Ana López",
                "documento": "12345678A",
                "telefono": "+34 600 111 222",
                "email": "ana@example.com",
                "activo": 1,
            }
        ]


def test_healthz_ok(monkeypatch):
    monkeypatch.delenv("CLINICDESK_API_KEY", raising=False)
    client = TestClient(create_app(servicio=_ServicioMock()))

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_sin_key_en_env_devuelve_503(monkeypatch):
    monkeypatch.delenv("CLINICDESK_API_KEY", raising=False)
    client = TestClient(create_app(servicio=_ServicioMock()))

    response = client.get("/api/v1/citas")

    assert response.status_code == 503


def test_api_key_incorrecta_devuelve_401(monkeypatch):
    monkeypatch.setenv("CLINICDESK_API_KEY", "clave-correcta")
    client = TestClient(create_app(servicio=_ServicioMock()))

    response = client.get("/api/v1/citas", headers={"X-API-Key": "clave-mala"})

    assert response.status_code == 401


def test_api_key_correcta_devuelve_200_y_redacta_pii(monkeypatch):
    monkeypatch.setenv("CLINICDESK_API_KEY", "clave-correcta")
    client = TestClient(create_app(servicio=_ServicioMock()))

    citas = client.get("/api/v1/citas", headers={"X-API-Key": "clave-correcta"})
    pacientes = client.get("/api/v1/pacientes", headers={"X-API-Key": "clave-correcta"})

    assert citas.status_code == 200
    assert pacientes.status_code == 200
    assert citas.json()[0]["paciente"] != "Ana López"
    assert pacientes.json()[0]["documento"] != "12345678A"
    assert pacientes.json()[0]["telefono"] != "+34 600 111 222"
    assert pacientes.json()[0]["email"] != "ana@example.com"
