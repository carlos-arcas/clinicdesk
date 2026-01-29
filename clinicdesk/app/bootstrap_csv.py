# app/bootstrap_csv.py
"""
Bootstrap de la UI CSV.

Crea:
- CsvService (application)
- CsvController (UI/controller)
"""

from __future__ import annotations

from app.controllers.csv_controller import CsvController
from application.usecases.csv.csv_service import CsvService
from container import AppContainer


def build_csv_controller(container: AppContainer, parent) -> CsvController:
    svc = CsvService(container)
    return CsvController(parent=parent, csv_service=svc)
