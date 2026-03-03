from __future__ import annotations

import sqlite3

from clinicdesk.app.queries.farmacia_queries import FarmaciaQueries


def build_farmacia_queries(connection: sqlite3.Connection) -> FarmaciaQueries:
    return FarmaciaQueries(connection)
