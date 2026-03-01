from __future__ import annotations

from clinicdesk.app.application.usecases.buscar_auditoria_accesos import BuscarAuditoriaAccesos
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos


class GatewayFake:
    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int]:
        assert filtros.usuario_contiene == "audit"
        assert limit == 10
        assert offset == 20
        return (
            [
                AuditoriaAccesoItemQuery(
                    timestamp_utc="2026-03-01T10:00:00+00:00",
                    usuario="audit-user",
                    modo_demo=True,
                    accion="VER_DETALLE_CITA",
                    entidad_tipo="CITA",
                    entidad_id="88",
                )
            ],
            55,
        )


def test_buscar_auditoria_accesos_usecase_mapea_resultado() -> None:
    usecase = BuscarAuditoriaAccesos(GatewayFake())

    resultado = usecase.execute(
        FiltrosAuditoriaAccesos(usuario_contiene="audit"),
        limit=10,
        offset=20,
    )

    assert resultado.total == 55
    assert len(resultado.items) == 1
    item = resultado.items[0]
    assert item.usuario == "audit-user"
    assert item.modo_demo is True
    assert item.accion == "VER_DETALLE_CITA"
    assert item.entidad_tipo == "CITA"
    assert item.entidad_id == "88"
