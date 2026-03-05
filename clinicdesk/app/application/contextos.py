from __future__ import annotations

from enum import StrEnum


class Contexto(StrEnum):
    CITAS = "citas"
    PACIENTES = "pacientes"
    AUDITORIA_SEGURIDAD = "auditoria_seguridad"
    PREFERENCIAS = "preferencias"
    ML_DEMO = "ml_demo"
    EXPORT = "export"
    COMPARTIDO = "compartido"


_PREFIJOS_POR_CONTEXTO: tuple[tuple[Contexto, tuple[str, ...]], ...] = (
    (
        Contexto.CITAS,
        (
            "clinicdesk/app/application/citas/",
            "clinicdesk/app/application/confirmaciones/",
            "clinicdesk/app/application/recordatorios/",
        ),
    ),
    (Contexto.CITAS, ("clinicdesk/app/application/features/citas_features",)),
    (Contexto.PACIENTES, ("clinicdesk/app/application/pacientes", "clinicdesk/app/application/historial_paciente/")),
    (
        Contexto.AUDITORIA_SEGURIDAD,
        (
            "clinicdesk/app/application/auditoria/",
            "clinicdesk/app/application/seguridad/",
            "clinicdesk/app/application/security.py",
        ),
    ),
    (Contexto.PREFERENCIAS, ("clinicdesk/app/application/preferencias/",)),
    (
        Contexto.ML_DEMO,
        (
            "clinicdesk/app/application/ml/",
            "clinicdesk/app/application/prediccion_",
            "clinicdesk/app/application/demo_data/",
            "clinicdesk/app/application/services/demo_",
        ),
    ),
    (Contexto.EXPORT, ("clinicdesk/app/application/csv/",)),
)


def _normalizar_ruta(path: str) -> str:
    ruta = path.replace("\\", "/").replace(".", "/")
    while "//" in ruta:
        ruta = ruta.replace("//", "/")
    return ruta.lower().strip("/")


def resolver_contexto_de_ruta(path: str) -> str:
    """Resuelve el contexto funcional a partir de una ruta o módulo."""
    ruta = _normalizar_ruta(path)
    for contexto, prefijos in _PREFIJOS_POR_CONTEXTO:
        if any(prefijo in ruta for prefijo in prefijos):
            return contexto.value
    return Contexto.COMPARTIDO.value
