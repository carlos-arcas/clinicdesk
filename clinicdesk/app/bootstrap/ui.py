from app.pages.page_registry import PageRegistry
from app.pages.page_host import PageHost
from app.pages.page_nav_sidebar import PageNavSidebar
from app.ui.main_window import MainWindow

from app.pages.citas.register import register as register_citas
from app.pages.farmacia.register import register as register_farmacia
# mañana:
# from app.pages.incidencias.register import register as register_incidencias


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
