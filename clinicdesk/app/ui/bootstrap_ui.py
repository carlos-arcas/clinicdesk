# clinicdesk/app/ui/bootstrap_ui.py

from clinicdesk.app.pages.citas.register import register as register_citas
from clinicdesk.app.pages.farmacia.register import register as register_farmacia
from clinicdesk.app.pages.home.register import register as register_home


def get_pages(container):
    pages = []

    register_home(pages, container)
    register_citas(pages, container)
    register_farmacia(pages, container)

    return pages
