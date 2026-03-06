from __future__ import annotations

import csv
from io import StringIO

from clinicdesk.app.application.usecases.centro_salud_operativa import CentroSaludOperativaDTO


def exportar_centro_salud_operativa_csv(resultado: CentroSaludOperativaDTO) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        (
            "kpi",
            "valor",
        )
    )
    kpis = resultado.kpis
    writer.writerow(("total_citas", str(kpis.total_citas)))
    writer.writerow(("citas_completadas", str(kpis.completadas)))
    writer.writerow(("citas_pendientes", str(kpis.pendientes)))
    writer.writerow(("canceladas_no_show", str(kpis.canceladas_no_show)))
    writer.writerow(("no_show", str(kpis.no_show)))
    writer.writerow(("tasa_no_asistencia_pct", f"{kpis.tasa_no_asistencia_pct:.2f}"))
    writer.writerow(("riesgo_medio_pct", "" if kpis.riesgo_medio_pct is None else f"{kpis.riesgo_medio_pct:.2f}"))
    writer.writerow(())
    writer.writerow(("severidad_alerta", "codigo_alerta", "total"))
    for alerta in resultado.alertas:
        writer.writerow((alerta.severidad, alerta.i18n_key, str(alerta.total)))
    return output.getvalue()
