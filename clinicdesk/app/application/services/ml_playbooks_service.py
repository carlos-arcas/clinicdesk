from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any


@dataclass(frozen=True, slots=True)
class PasoPlaybookML:
    clave: str
    accion_clave: str
    nombre_key: str
    que_hace_key: str
    por_que_importa_key: str
    necesitas_key: str
    resultado_key: str
    mirar_despues_key: str
    cta_key: str
    estado: str
    habilitado: bool
    motivo_estado_key: str


@dataclass(frozen=True, slots=True)
class PlaybookML:
    codigo: str
    titulo_key: str
    descripcion_key: str
    para_que_key: str
    cuando_usar_key: str
    prerequisitos_keys: tuple[str, ...]
    criterio_finalizacion_key: str
    estado_general: str
    siguiente_paso_clave: str
    pasos: tuple[PasoPlaybookML, ...]


class PlaybooksMLService:
    _SECUENCIAS = {
        "demo_completa": ("prepare", "train", "score", "drift", "export"),
        "entrenar_modelo_nuevo": ("prepare", "train", "score"),
        "puntuar_con_seguridad": ("prepare", "train", "score"),
        "revisar_drift_reentrenar": ("drift", "train", "score"),
        "exportar_bi": ("score", "export"),
    }

    def construir_playbooks(self, estado_pipeline: Any) -> tuple[PlaybookML, ...]:
        playbooks: list[PlaybookML] = []
        for codigo, acciones in self._SECUENCIAS.items():
            pasos = self._pasos_playbook(codigo, acciones, estado_pipeline)
            base = f"demo_ml.playbook.{codigo}"
            playbooks.append(
                PlaybookML(
                    codigo=codigo,
                    titulo_key=f"{base}.titulo",
                    descripcion_key=f"{base}.descripcion",
                    para_que_key=f"{base}.para_que",
                    cuando_usar_key=f"{base}.cuando_usar",
                    prerequisitos_keys=(f"{base}.prerequisito_1", f"{base}.prerequisito_2"),
                    criterio_finalizacion_key=f"{base}.finalizacion",
                    estado_general=self._estado_general(pasos),
                    siguiente_paso_clave=self._siguiente_paso(pasos),
                    pasos=pasos,
                )
            )
        return tuple(playbooks)

    def sugerir_playbook(self, playbooks: tuple[PlaybookML, ...]) -> str:
        if not playbooks:
            return "demo_completa"
        prioridad = {"recomendado": 4, "disponible": 3, "bloqueado": 2, "completado": 1, "innecesario": 0}

        def puntaje(playbook: PlaybookML) -> tuple[int, int]:
            mejor_estado = max((prioridad.get(paso.estado, 0) for paso in playbook.pasos), default=0)
            return mejor_estado, len(playbook.pasos)

        return sorted(playbooks, key=puntaje, reverse=True)[0].codigo

    def _pasos_playbook(self, codigo: str, acciones: tuple[str, ...], estado_pipeline: Any) -> tuple[PasoPlaybookML, ...]:
        pasos: list[PasoPlaybookML] = []
        for accion in acciones:
            estado, habilitado, motivo = self._resolver_estado_paso(codigo, accion, estado_pipeline)
            base = f"demo_ml.playbook.paso.{accion}"
            pasos.append(
                PasoPlaybookML(
                    clave=f"{codigo}.{accion}",
                    accion_clave=accion,
                    nombre_key=f"{base}.nombre",
                    que_hace_key=f"{base}.que_hace",
                    por_que_importa_key=f"{base}.por_que_importa",
                    necesitas_key=f"{base}.necesitas",
                    resultado_key=f"{base}.resultado",
                    mirar_despues_key=f"{base}.mirar_despues",
                    cta_key=f"{base}.cta",
                    estado=estado,
                    habilitado=habilitado,
                    motivo_estado_key=motivo,
                )
            )
        recomendado = next((paso for paso in pasos if paso.estado == "disponible"), None)
        if recomendado is None:
            return tuple(pasos)
        return tuple(self._marcar_recomendado(paso, recomendado.clave) for paso in pasos)

    def _marcar_recomendado(self, paso: PasoPlaybookML, clave_objetivo: str) -> PasoPlaybookML:
        if paso.clave != clave_objetivo:
            return paso
        return replace(paso, estado="recomendado")

    def _resolver_estado_paso(self, codigo: str, accion: str, estado_pipeline: Any) -> tuple[str, bool, str]:
        paso_base = next((item for item in estado_pipeline.pasos if item.clave == accion), None)
        if paso_base is None:
            return "innecesario", False, "demo_ml.playbook.estado.motivo_innecesario"
        if accion == "drift" and not estado_pipeline.drift_disponible:
            return "innecesario", False, "demo_ml.playbook.estado.motivo_drift_no_aplica"
        if codigo == "revisar_drift_reentrenar" and accion == "train" and not estado_pipeline.drift_disponible:
            return "innecesario", False, "demo_ml.playbook.estado.motivo_entrenar_no_aplica"
        if codigo == "exportar_bi" and accion == "export" and not estado_pipeline.score_disponible:
            return "bloqueado", False, "demo_ml.playbook.estado.motivo_score_requerido"
        if paso_base.estado == "completado":
            return "completado", True, "demo_ml.playbook.estado.motivo_completado"
        if not paso_base.habilitado:
            return "bloqueado", False, "demo_ml.playbook.estado.motivo_bloqueado"
        return "disponible", True, "demo_ml.playbook.estado.motivo_disponible"

    def _estado_general(self, pasos: tuple[PasoPlaybookML, ...]) -> str:
        estados = {paso.estado for paso in pasos}
        if "recomendado" in estados or "disponible" in estados:
            return "activo"
        if "bloqueado" in estados:
            return "bloqueado"
        if estados <= {"completado", "innecesario"}:
            return "completado"
        return "pendiente"

    def _siguiente_paso(self, pasos: tuple[PasoPlaybookML, ...]) -> str:
        for estado in ("recomendado", "disponible", "bloqueado"):
            paso = next((item for item in pasos if item.estado == estado), None)
            if paso is not None:
                return paso.accion_clave
        return "summary"
