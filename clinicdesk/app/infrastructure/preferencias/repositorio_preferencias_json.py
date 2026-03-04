from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from clinicdesk.app.application.preferencias.preferencias_usuario import PreferenciasRepository, PreferenciasUsuario


class RepositorioPreferenciasJson(PreferenciasRepository):
    def __init__(self, ruta_archivo: Path) -> None:
        self._ruta_archivo = Path(ruta_archivo)

    def get(self, perfil: str) -> PreferenciasUsuario:
        data = self._cargar_todo()
        raw = data.get(perfil)
        if not isinstance(raw, dict):
            return PreferenciasUsuario()
        return PreferenciasUsuario(
            pagina_ultima=str(raw.get("pagina_ultima") or "home"),
            filtros_pacientes=dict(raw.get("filtros_pacientes") or {}),
            filtros_confirmaciones=dict(raw.get("filtros_confirmaciones") or {}),
            last_search_by_context=dict(raw.get("last_search_by_context") or {}),
            columnas_por_contexto={
                str(clave): [str(col) for col in columnas]
                for clave, columnas in dict(raw.get("columnas_por_contexto") or {}).items()
                if isinstance(columnas, list)
            },
        )

    def set(self, perfil: str, preferencias: PreferenciasUsuario) -> None:
        data = self._cargar_todo()
        data[perfil] = asdict(preferencias)
        self._ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        self._ruta_archivo.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _cargar_todo(self) -> dict[str, dict]:
        if not self._ruta_archivo.exists():
            return {}
        try:
            loaded = json.loads(self._ruta_archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return loaded if isinstance(loaded, dict) else {}
