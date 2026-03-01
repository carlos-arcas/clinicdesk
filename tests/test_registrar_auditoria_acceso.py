from __future__ import annotations

from dataclasses import dataclass, field

from clinicdesk.app.application.auditoria_acceso import AccionAuditoriaAcceso, EntidadAuditoriaAcceso, EventoAuditoriaAcceso
from clinicdesk.app.application.security import Role, UserContext
from clinicdesk.app.application.usecases.registrar_auditoria_acceso import RegistrarAuditoriaAcceso


@dataclass
class RepositorioAuditoriaAccesoFake:
    eventos: list[EventoAuditoriaAcceso] = field(default_factory=list)

    def registrar(self, evento: EventoAuditoriaAcceso) -> None:
        self.eventos.append(evento)


def test_registrar_auditoria_acceso_genera_evento_esperado() -> None:
    repo = RepositorioAuditoriaAccesoFake()
    usecase = RegistrarAuditoriaAcceso(repo)
    contexto = UserContext(role=Role.ADMIN, username="auditor", demo_mode=True)

    usecase.execute(
        contexto_usuario=contexto,
        accion=AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE,
        entidad_tipo=EntidadAuditoriaAcceso.PACIENTE,
        entidad_id=77,
    )

    assert len(repo.eventos) == 1
    evento = repo.eventos[0]
    assert evento.usuario == "auditor"
    assert evento.modo_demo is True
    assert evento.accion == AccionAuditoriaAcceso.VER_HISTORIAL_PACIENTE
    assert evento.entidad_tipo == EntidadAuditoriaAcceso.PACIENTE
    assert evento.entidad_id == "77"
    assert evento.timestamp_utc
