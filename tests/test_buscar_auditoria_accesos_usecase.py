from __future__ import annotations

from datetime import UTC, datetime

from clinicdesk.app.application.usecases.buscar_auditoria_accesos import BuscarAuditoriaAccesos
from clinicdesk.app.application.usecases.preflight_integridad_auditoria import (
    EstadoIntegridadAuditoria,
    IntegridadAuditoriaComprometidaError,
)
from clinicdesk.app.queries.auditoria_accesos_queries import AuditoriaAccesoItemQuery, FiltrosAuditoriaAccesos


class GatewayFake:
    def __init__(self) -> None:
        self.recibido: FiltrosAuditoriaAccesos | None = None
        self.calcular_total_recibido: bool | None = None

    def buscar_auditoria_accesos(
        self,
        filtros: FiltrosAuditoriaAccesos,
        limit: int,
        offset: int,
        *,
        calcular_total: bool = True,
    ) -> tuple[list[AuditoriaAccesoItemQuery], int | None]:
        self.recibido = filtros
        self.calcular_total_recibido = calcular_total
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
            55 if calcular_total else None,
        )


def test_buscar_auditoria_accesos_usecase_mapea_resultado() -> None:
    usecase = BuscarAuditoriaAccesos(GatewayFake())
    resultado = usecase.execute(
        FiltrosAuditoriaAccesos(usuario_contiene="audit"), limit=10, offset=20, preset_rango="personalizado"
    )

    assert resultado.total == 55
    assert len(resultado.items) == 1
    item = resultado.items[0]
    assert item.usuario == "audit-user"
    assert item.modo_demo is True
    assert item.accion == "VER_DETALLE_CITA"
    assert item.entidad_tipo == "CITA"
    assert item.entidad_id == "88"


def test_buscar_auditoria_aplica_preset_hoy() -> None:
    gateway = GatewayFake()
    BuscarAuditoriaAccesos(gateway).execute(
        FiltrosAuditoriaAccesos(usuario_contiene="audit"), limit=10, offset=20, preset_rango="hoy"
    )

    assert gateway.recibido is not None
    assert isinstance(gateway.recibido.desde_utc, datetime)
    assert isinstance(gateway.recibido.hasta_utc, datetime)
    assert gateway.recibido.desde_utc.tzinfo == UTC


def test_buscar_auditoria_reutiliza_total_conocido() -> None:
    gateway = GatewayFake()
    resultado = BuscarAuditoriaAccesos(gateway).execute(
        FiltrosAuditoriaAccesos(usuario_contiene="audit"),
        limit=10,
        offset=20,
        total_conocido=120,
    )

    assert gateway.calcular_total_recibido is False
    assert resultado.total == 120


class VerificadorIntegridadFake:
    def __init__(self, resultado: EstadoIntegridadAuditoria) -> None:
        self.resultado = resultado
        self.llamadas = 0

    def verificar_integridad_auditoria(self) -> EstadoIntegridadAuditoria:
        self.llamadas += 1
        return self.resultado


def test_buscar_auditoria_ejecuta_preflight_integridad() -> None:
    verificador = VerificadorIntegridadFake(EstadoIntegridadAuditoria(ok=True))
    usecase = BuscarAuditoriaAccesos(GatewayFake(), verificador_integridad=verificador)

    usecase.execute(FiltrosAuditoriaAccesos(usuario_contiene="audit"), limit=10, offset=20)

    assert verificador.llamadas == 1


def test_buscar_auditoria_bloquea_si_cadena_comprometida() -> None:
    verificador = VerificadorIntegridadFake(
        EstadoIntegridadAuditoria(ok=False, tabla="auditoria_accesos", primer_fallo_id=7)
    )
    usecase = BuscarAuditoriaAccesos(GatewayFake(), verificador_integridad=verificador)

    try:
        usecase.execute(FiltrosAuditoriaAccesos(usuario_contiene="audit"), limit=10, offset=20)
        raise AssertionError("se esperaba IntegridadAuditoriaComprometidaError")
    except IntegridadAuditoriaComprometidaError as exc:
        assert exc.reason_code == "auditoria_integridad_comprometida"
        assert exc.tabla == "auditoria_accesos"
        assert exc.primer_fallo_id == 7
