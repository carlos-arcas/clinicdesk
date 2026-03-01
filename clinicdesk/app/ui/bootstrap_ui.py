# clinicdesk/app/ui/bootstrap_ui.py

from clinicdesk.app.pages.citas.register import register as register_citas
from clinicdesk.app.pages.farmacia.register import register as register_farmacia
from clinicdesk.app.pages.home.register import register as register_home
from clinicdesk.app.pages.incidencias.register import register as register_incidencias
from clinicdesk.app.pages.pacientes.register import register as register_pacientes
from clinicdesk.app.pages.medicos.register import register as register_medicos
from clinicdesk.app.pages.personal.register import register as register_personal
from clinicdesk.app.pages.salas.register import register as register_salas
from clinicdesk.app.pages.turnos.register import register as register_turnos
from clinicdesk.app.pages.ausencias.register import register as register_ausencias
from clinicdesk.app.pages.medicamentos.register import register as register_medicamentos
from clinicdesk.app.pages.materiales.register import register as register_materiales
from clinicdesk.app.pages.recetas.register import register as register_recetas
from clinicdesk.app.pages.dispensaciones.register import register as register_dispensaciones
from clinicdesk.app.pages.demo_ml.register import register as register_demo_ml
from clinicdesk.app.pages.auditoria.register import register as register_auditoria
from clinicdesk.app.pages.prediccion_ausencias.register import register as register_prediccion_ausencias
from clinicdesk.app.i18n import I18nManager
from clinicdesk.app.pages.pages_registry import PageRegistry


def get_pages(container, i18n: I18nManager):
    registry = PageRegistry()

    register_home(registry, container)
    register_pacientes(registry, container)
    register_citas(registry, container)
    register_medicos(registry, container)
    register_personal(registry, container)
    register_salas(registry, container)
    register_farmacia(registry, container)
    register_medicamentos(registry, container)
    register_materiales(registry, container)
    register_recetas(registry, container)
    register_dispensaciones(registry, container)
    register_turnos(registry, container)
    register_ausencias(registry, container)
    register_incidencias(registry, container)
    register_demo_ml(registry, container)
    register_auditoria(registry, container)
    register_prediccion_ausencias(registry, container, i18n)

    return registry.list()
