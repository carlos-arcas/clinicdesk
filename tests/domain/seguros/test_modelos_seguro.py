from clinicdesk.app.domain.seguros import PlanSeguro, TipoPlanSeguro
from clinicdesk.app.application.seguros.catalogo_planes import CatalogoPlanesSeguro


def test_catalogo_expone_planes_tipados() -> None:
    catalogo = CatalogoPlanesSeguro()

    planes = catalogo.listar_planes()

    assert planes
    assert all(isinstance(plan, PlanSeguro) for plan in planes)
    assert {plan.tipo_plan for plan in planes} == {TipoPlanSeguro.CLINICA, TipoPlanSeguro.EXTERNO}
