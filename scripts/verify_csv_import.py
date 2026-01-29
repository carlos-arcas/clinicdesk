from __future__ import annotations

import csv
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
if REPO_ROOT.as_posix() not in sys.path:
    sys.path.insert(0, REPO_ROOT.as_posix())

from clinicdesk.app.application.csv.csv_service import CsvService
from clinicdesk.app.bootstrap import schema_path
from clinicdesk.app.container import build_container
from clinicdesk.app.domain.enums import TipoDocumento
from clinicdesk.app.domain.modelos import Paciente
from clinicdesk.app.infrastructure.sqlite import db as sqlite_db


def _write_csv(path: Path, *, rows: list[dict[str, str]]) -> None:
    headers = [
        "tipo_documento",
        "documento",
        "nombre",
        "apellidos",
        "telefono",
        "email",
        "fecha_nacimiento",
        "direccion",
        "activo",
        "num_historia",
        "alergias",
        "observaciones",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    paciente = Paciente(
        tipo_documento=TipoDocumento.DNI,
        documento="12345678A",
        nombre="Ada",
        apellidos="Lovelace",
        num_historia="HIST-001",
        alergias="Polen",
        observaciones="Paciente de prueba",
    )
    paciente.validar()

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        db_path = temp_path / "clinicdesk_test.sqlite"
        con = sqlite_db.bootstrap(db_path, schema_path())
        container = build_container(con)

        csv_path = temp_path / "pacientes.csv"
        _write_csv(
            csv_path,
            rows=[
                {
                    "tipo_documento": "DNI",
                    "documento": "11111111A",
                    "nombre": "Ana",
                    "apellidos": "García",
                    "telefono": "600000001",
                    "email": "ana@example.com",
                    "fecha_nacimiento": "1990-01-01",
                    "direccion": "Calle Uno",
                    "activo": "1",
                    "num_historia": "NH-001",
                    "alergias": "Penicilina",
                    "observaciones": "Observación 1",
                },
                {
                    "tipo_documento": "NIE",
                    "documento": "X1234567B",
                    "nombre": "Luis",
                    "apellidos": "Pérez",
                    "telefono": "600000002",
                    "email": "luis@example.com",
                    "fecha_nacimiento": "1985-05-10",
                    "direccion": "Calle Dos",
                    "activo": "1",
                    "num_historia": "NH-002",
                    "alergias": "",
                    "observaciones": "",
                },
            ],
        )

        service = CsvService(container)
        result = service.import_pacientes(csv_path.as_posix())
        assert result.created == 2, f"Esperado 2 creados, obtenido {result.created}"
        assert result.errors == [], f"Esperado 0 errores, obtenido {result.errors}"

        pacientes = container.pacientes_repo.list_all(solo_activos=False)
        assert len(pacientes) == 2, f"Esperado 2 pacientes en DB, obtenido {len(pacientes)}"

        container.close()


if __name__ == "__main__":
    main()
