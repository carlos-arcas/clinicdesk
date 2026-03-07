from __future__ import annotations

import json
from dataclasses import dataclass, field

from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.telemetria import EventoTelemetriaDTO
from clinicdesk.app.application.usecases.registrar_telemetria import RegistrarTelemetria


@dataclass
class RepositorioTelemetriaFake:
    eventos: list[EventoTelemetriaDTO] = field(default_factory=list)

    def registrar(self, evento: EventoTelemetriaDTO) -> None:
        self.eventos.append(evento)


def _contexto() -> UserContext:
    return UserContext(role=Role.ADMIN, username="auditor", demo_mode=False)


def test_registrar_telemetria_conserva_contexto_permitido() -> None:
    repo = RepositorioTelemetriaFake()
    usecase = RegistrarTelemetria(repo)

    usecase.ejecutar(
        contexto_usuario=_contexto(),
        evento="gestion_abrir_cita",
        contexto="page=gestion;resultado=ok;vista=listado",
    )

    assert repo.eventos[0].contexto == "page=gestion;resultado=ok;vista=listado"


def test_registrar_telemetria_elimina_claves_sensibles_y_marca_trazabilidad() -> None:
    repo = RepositorioTelemetriaFake()
    usecase = RegistrarTelemetria(repo)

    usecase.ejecutar(
        contexto_usuario=_contexto(),
        evento="gestion_abrir_cita",
        contexto="page=gestion;email=ana@test.com;telefono=600123123",
    )

    contexto = repo.eventos[0].contexto or ""
    assert "email=" not in contexto
    assert "telefono=" not in contexto
    assert "redaccion_aplicada=true" in contexto


def test_registrar_telemetria_redacta_pii_en_texto_libre() -> None:
    repo = RepositorioTelemetriaFake()
    usecase = RegistrarTelemetria(repo)

    usecase.ejecutar(
        contexto_usuario=_contexto(),
        evento="gestion_abrir_cita",
        contexto="detalle=contacto ana@test.com dni 12345678Z movil 600123123",
    )

    contexto = repo.eventos[0].contexto or ""
    assert "ana@test.com" not in contexto
    assert "12345678Z" not in contexto
    assert "600123123" not in contexto
    assert "[REDACTED_EMAIL]" in contexto
    assert "[REDACTED_DNI]" in contexto
    assert "[REDACTED_PHONE]" in contexto


def test_registrar_telemetria_sanea_estructuras_anidadas_json() -> None:
    repo = RepositorioTelemetriaFake()
    usecase = RegistrarTelemetria(repo)

    contexto_json = json.dumps(
        {
            "page": "auditoria",
            "contexto": {
                "tab": "resumen",
                "dni": "12345678Z",
                "detalle": "email ana@test.com",
            },
            "detalle": ["telefono 600123123", {"movil": "611111111"}],
        },
        ensure_ascii=False,
    )

    usecase.ejecutar(
        contexto_usuario=_contexto(),
        evento="auditoria_export",
        contexto=contexto_json,
    )

    contexto_guardado = json.loads(repo.eventos[0].contexto or "{}")
    assert contexto_guardado["page"] == "auditoria"
    assert "dni" not in contexto_guardado["contexto"]
    assert "ana@test.com" not in contexto_guardado["contexto"]["detalle"]
    assert "600123123" not in contexto_guardado["detalle"][0]
    assert len(contexto_guardado["detalle"]) == 1
    assert contexto_guardado["redaccion_aplicada"] is True
