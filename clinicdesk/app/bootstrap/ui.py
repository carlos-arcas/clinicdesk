from clinicdesk.app.pages.pages_registry import PageRegistry
from clinicdesk.app.pages.page_host import PageHost
from clinicdesk.app.pages.page_nav_sidebar import PageNavSidebar
from clinicdesk.app.ui.main_window import MainWindow

from clinicdesk.app.pages.citas.register import register as register_citas
from clinicdesk.app.pages.farmacia.register import register as register_farmacia
# mañana:
# from clinicdesk.app.pages.incidencias.register import register as register_incidencias


def build_main_window(container):
    registry = PageRegistry()

    # Auto-registro
    register_citas(registry, container)
    register_farmacia(registry, container)

    host = PageHost(registry)
    sidebar = PageNavSidebar(registry, host)

    # primera página
    host.show_page("citas")

    return MainWindow(sidebar=sidebar, host=host)
