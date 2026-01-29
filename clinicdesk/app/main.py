from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from clinicdesk.app.bootstrap import bootstrap_database
from clinicdesk.app.container import build_container
from clinicdesk.app.ui.main_window import MainWindow
from clinicdesk.app.ui.theme import load_qss


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(load_qss())

    con = bootstrap_database(apply_schema=True)
    container = build_container(con)

    win = MainWindow(container)
    win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
