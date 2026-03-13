from __future__ import annotations

from clinicdesk.app.application.seguridad_salida import serializar_cita_api_demo, serializar_paciente_api_demo
from clinicdesk.app.application.services.demo_ml_facade import DemoMLFacade


class _ReadGatewayFugaMock:
    def list_doctors(self, query: str | None, limit: int) -> list[dict[str, object]]:
        return [
            {
                "id": 1,
                "documento": "12345678A",
                "documento_hash": "hash",
                "documento_enc": "cipher",
                "nombre_completo": "Dra. Ana López",
                "telefono": "+34 600 111 222",
                "telefono_enc": "cipher2",
                "especialidad": "Cardiología",
                "activo": True,
            }
        ]

    def list_patients(self, query: str | None, limit: int) -> list[dict[str, object]]:
        return [
            {
                "id": 2,
                "documento": "99887766B",
                "documento_hash": "hash",
                "nombre_completo": "Juan Pérez",
                "telefono": "+34 700 111 333",
                "email": "juan@example.com",
                "activo": True,
            }
        ]

    def list_appointments(
        self,
        query: str | None,
        from_date: str | None,
        to_date: str | None,
        limit: int,
    ) -> list[dict[str, object]]:
        return [
            {
                "id": 5,
                "inicio": "2026-01-10 09:00:00",
                "fin": "2026-01-10 09:15:00",
                "paciente_nombre": "Juan Pérez",
                "medico_nombre": "Dra. Ana López",
                "estado": "PENDIENTE",
                "motivo": "Control de diabetes HC-9999",
            }
        ]

    def list_incidences(self, query: str | None, limit: int) -> list[dict[str, object]]:
        return [
            {
                "id": 8,
                "fecha_hora": "2026-01-10 08:00:00",
                "tipo": "OPERATIVA",
                "severidad": "MEDIA",
                "estado": "ABIERTA",
                "descripcion": "Paciente Juan Pérez no presenta DNI 12345678A",
            }
        ]


class _NoOp:
    def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("No debería invocarse en este test")


def _facade() -> DemoMLFacade:
    return DemoMLFacade(
        read_gateway=_ReadGatewayFugaMock(),
        seed_demo_uc=_NoOp(),
        build_dataset=_NoOp(),
        feature_store_service=_NoOp(),
        train_uc=_NoOp(),
        score_uc=_NoOp(),
        drift_uc=_NoOp(),
    )


def test_serializadores_api_demo_aplican_whitelist_y_no_filtran_columnas_tecnicas() -> None:
    cita = serializar_cita_api_demo(
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
            "motivo": "dato no permitido",
            "documento_enc": "cipher",
        }
    )
    paciente = serializar_paciente_api_demo(
        {
            "id": 2,
            "nombre": "Ana",
            "apellidos": "López",
            "nombre_completo": "Ana López",
            "documento": "12345678A",
            "telefono": "+34 600 111 222",
            "email": "ana@example.com",
            "activo": 1,
            "telefono_enc": "cipher",
            "documento_hash": "hash",
        }
    )

    assert set(cita.keys()) == {
        "id",
        "fecha",
        "hora_inicio",
        "hora_fin",
        "estado",
        "sala",
        "medico",
        "paciente",
        "tiene_incidencias",
    }
    assert "documento_enc" not in cita
    assert paciente["documento"] != "12345678A"
    assert paciente["telefono"] != "+34 600 111 222"
    assert paciente["email"] != "ana@example.com"
    assert "documento_hash" not in paciente
    assert "telefono_enc" not in paciente


def test_demo_ml_facade_minimiza_y_redacta_en_read_models() -> None:
    facade = _facade()

    doctor = facade.list_doctors()[0]
    patient = facade.list_patients()[0]
    cita = facade.list_appointments()[0]
    incidencia = facade.list_incidences()[0]

    assert doctor.documento != "12345678A"
    assert doctor.telefono != "+34 600 111 222"
    assert patient.documento != "99887766B"
    assert patient.telefono != "+34 700 111 333"
    assert "***" in cita.motivo
    assert "12345678A" not in incidencia.descripcion
