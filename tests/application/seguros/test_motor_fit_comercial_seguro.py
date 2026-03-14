from clinicdesk.app.application.seguros.fit_comercial import MotorFitComercialSeguro, SolicitudFitComercialSeguro
from clinicdesk.app.application.seguros.usecases import AnalizarMigracionSeguroUseCase, SolicitudAnalisisMigracionSeguro
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro
from clinicdesk.app.domain.seguros.segmentacion import (
    EncajePlanSeguro,
    FriccionMigracionSeguro,
    MotivacionCompraSeguro,
    NecesidadPrincipalSeguro,
    ObjecionComercialSeguro,
    OrigenClienteSeguro,
    PerfilComercialSeguro,
    SegmentoClienteSeguro,
    SensibilidadPrecioSeguro,
)


def _simulacion():
    usecase = AnalizarMigracionSeguroUseCase(CatalogoPlanesSeguro())
    res = usecase.execute(
        SolicitudAnalisisMigracionSeguro(
            plan_origen_id="externo_basico",
            plan_destino_id="clinica_esencial",
            edad=34,
            residencia_pais="ES",
            historial_impagos=False,
            preexistencias_graves=False,
        )
    )
    return res.simulacion


def test_motor_fit_comercial_devuelve_encaje_y_argumentos() -> None:
    motor = MotorFitComercialSeguro()
    solicitud = SolicitudFitComercialSeguro(
        perfil=PerfilComercialSeguro(
            segmento_cliente=SegmentoClienteSeguro.ASEGURADO_EXTERNO_MIGRAR,
            origen_cliente=OrigenClienteSeguro.REFERIDO,
            necesidad_principal=NecesidadPrincipalSeguro.CONTINUIDAD_MEDICA,
            motivaciones=(MotivacionCompraSeguro.CONFIANZA_EN_CLINICA,),
            objecion_principal=ObjecionComercialSeguro.NO_TIENE_TIEMPO,
            sensibilidad_precio=SensibilidadPrecioSeguro.BAJA,
            friccion_migracion=FriccionMigracionSeguro.BAJA,
        ),
        simulacion_migracion=_simulacion(),
    )

    evaluacion = motor.evaluar(solicitud)

    assert evaluacion.encaje_plan in set(EncajePlanSeguro)
    assert evaluacion.argumentos_valor
    assert isinstance(evaluacion.conviene_insistir, bool)
