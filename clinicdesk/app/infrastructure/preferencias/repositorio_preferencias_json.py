from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from clinicdesk.app.application.preferencias.preferencias_usuario import PreferenciasRepository, PreferenciasUsuario

_ENV_PREFS_PATH = "CLINICDESK_PREFS_PATH"
_RUTA_PREFS_DEFAULT = Path("data/user_prefs.json")
_PERFIL_DEFAULT = "default"


class RepositorioPreferenciasJson(PreferenciasRepository):
    def __init__(self, ruta_archivo: Path | None = None) -> None:
        ruta_env = os.getenv(_ENV_PREFS_PATH)
        self._ruta_archivo = Path(ruta_env) if ruta_env else Path(ruta_archivo or _RUTA_PREFS_DEFAULT)

    def get(self, perfil_id: str | None) -> PreferenciasUsuario:
        data = self._cargar_todo()
        raw = data.get(self._perfil(perfil_id))
        if not isinstance(raw, dict):
            return PreferenciasUsuario()
        return PreferenciasUsuario(
            pagina_ultima=self._to_optional_str(raw.get("pagina_ultima")),
            filtros_pacientes=self._to_mapa_filtros(raw.get("filtros_pacientes")),
            filtros_confirmaciones=self._to_mapa_filtros(raw.get("filtros_confirmaciones")),
            last_search_by_context=self._to_mapa_search(raw.get("last_search_by_context")),
            columnas_por_contexto=self._to_mapa_columnas(raw.get("columnas_por_contexto")),
        )

    def set(self, perfil_id: str | None, preferencias: PreferenciasUsuario) -> None:
        data = self._cargar_todo()
        data[self._perfil(perfil_id)] = asdict(preferencias)
        self._ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._ruta_archivo.with_suffix(f"{self._ruta_archivo.suffix}.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, self._ruta_archivo)

    def _cargar_todo(self) -> dict[str, dict]:
        if not self._ruta_archivo.exists():
            return {}
        try:
            loaded = json.loads(self._ruta_archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def _perfil(perfil_id: str | None) -> str:
        return perfil_id or _PERFIL_DEFAULT

    @staticmethod
    def _to_optional_str(value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return value
        return None

    @staticmethod
    def _to_mapa_filtros(value: object) -> dict[str, str | int | bool | None]:
        if not isinstance(value, dict):
            return {}
        resultado: dict[str, str | int | bool | None] = {}
        for clave, elemento in value.items():
            if isinstance(clave, str) and (isinstance(elemento, (str, int, bool)) or elemento is None):
                resultado[clave] = elemento
        return resultado

    @staticmethod
    def _to_mapa_search(value: object) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        return {str(clave): str(elemento) for clave, elemento in value.items() if isinstance(elemento, str)}

    @staticmethod
    def _to_mapa_columnas(value: object) -> dict[str, dict[str, int | str]]:
        if not isinstance(value, dict):
            return {}
        resultado: dict[str, dict[str, int | str]] = {}
        for contexto, columnas in value.items():
            if not isinstance(contexto, str) or not isinstance(columnas, dict):
                continue
            contexto_valido: dict[str, int | str] = {}
            for clave_columna, valor_columna in columnas.items():
                if isinstance(clave_columna, str) and isinstance(valor_columna, (int, str)):
                    contexto_valido[clave_columna] = valor_columna
            resultado[contexto] = contexto_valido
        return resultado
