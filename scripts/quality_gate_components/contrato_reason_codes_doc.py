from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MARCADOR_INICIO_GLOSARIO_REASON_CODES = "<!-- GATE_REASON_CODES_GLOSARIO:START -->"
MARCADOR_FIN_GLOSARIO_REASON_CODES = "<!-- GATE_REASON_CODES_GLOSARIO:END -->"
MARCADOR_INICIO_SEMANTICA_BLOQUEO_OPERATIVO = "<!-- GATE_BLOQUEO_OPERATIVO_SEMANTICA:START -->"
MARCADOR_FIN_SEMANTICA_BLOQUEO_OPERATIVO = "<!-- GATE_BLOQUEO_OPERATIVO_SEMANTICA:END -->"


class ErrorContratoReasonCodesDoc(ValueError):
    """Error de contrato entre fuente canónica y glosario documental."""


@dataclass(frozen=True)
class ResultadoCoherenciaReasonCodes:
    faltantes_en_doc: tuple[str, ...]
    sobrantes_en_doc: tuple[str, ...]

    @property
    def en_sync(self) -> bool:
        return not self.faltantes_en_doc and not self.sobrantes_en_doc


def cargar_reason_codes_documentados(ruta_doc: Path) -> tuple[str, ...]:
    return extraer_reason_codes_documentados(ruta_doc.read_text(encoding="utf-8"))


def extraer_reason_codes_documentados(texto_doc: str) -> tuple[str, ...]:
    lineas_bloque = _extraer_lineas_bloque_glosario(texto_doc)
    codigos: set[str] = set()
    for linea in lineas_bloque:
        linea_normalizada = linea.strip()
        if not linea_normalizada.startswith("| `"):
            continue
        columnas = [columna.strip() for columna in linea_normalizada.split("|")]
        if len(columnas) < 3:
            continue
        codigo = columnas[1].strip("`")
        if codigo == "reason_code":
            continue
        codigos.add(codigo)
    if not codigos:
        raise ErrorContratoReasonCodesDoc(
            "Bloque de glosario de reason_code sin filas parseables; revisa delimitadores y formato de tabla."
        )
    return tuple(sorted(codigos))


def comparar_reason_codes(canonicos: tuple[str, ...], documentados: tuple[str, ...]) -> ResultadoCoherenciaReasonCodes:
    set_canonicos = set(canonicos)
    set_documentados = set(documentados)
    return ResultadoCoherenciaReasonCodes(
        faltantes_en_doc=tuple(sorted(set_canonicos - set_documentados)),
        sobrantes_en_doc=tuple(sorted(set_documentados - set_canonicos)),
    )


def validar_coherencia_reason_codes_doc(ruta_doc: Path, canonicos: tuple[str, ...]) -> None:
    documentados = cargar_reason_codes_documentados(ruta_doc)
    resultado = comparar_reason_codes(canonicos=canonicos, documentados=documentados)
    if resultado.en_sync:
        return
    detalles = []
    if resultado.faltantes_en_doc:
        detalles.append(f"sin documentar={resultado.faltantes_en_doc}")
    if resultado.sobrantes_en_doc:
        detalles.append(f"sin fuente canonica={resultado.sobrantes_en_doc}")
    raise ErrorContratoReasonCodesDoc("Contrato reason_code doc↔código inconsistente: " + "; ".join(detalles))


def cargar_snippets_semantica_bloqueo_operativo(ruta_doc: Path) -> tuple[str, ...]:
    return extraer_snippets_semantica_bloqueo_operativo(ruta_doc.read_text(encoding="utf-8"))


def extraer_snippets_semantica_bloqueo_operativo(texto_doc: str) -> tuple[str, ...]:
    lineas_bloque = _extraer_lineas_entre_marcadores(
        texto_doc=texto_doc,
        marcador_inicio=MARCADOR_INICIO_SEMANTICA_BLOQUEO_OPERATIVO,
        marcador_fin=MARCADOR_FIN_SEMANTICA_BLOQUEO_OPERATIVO,
        nombre_bloque="semántica mínima de bloqueo operativo",
    )
    snippets: list[str] = []
    for linea in lineas_bloque:
        linea_normalizada = linea.strip()
        if not linea_normalizada.startswith("- `") or not linea_normalizada.endswith("`"):
            continue
        snippets.append(linea_normalizada[3:-1])
    if not snippets:
        raise ErrorContratoReasonCodesDoc(
            "Bloque de semántica mínima de bloqueo operativo sin snippets parseables."
        )
    return tuple(snippets)


def _extraer_lineas_bloque_glosario(texto_doc: str) -> tuple[str, ...]:
    return _extraer_lineas_entre_marcadores(
        texto_doc=texto_doc,
        marcador_inicio=MARCADOR_INICIO_GLOSARIO_REASON_CODES,
        marcador_fin=MARCADOR_FIN_GLOSARIO_REASON_CODES,
        nombre_bloque="glosario de reason_code",
    )


def _extraer_lineas_entre_marcadores(
    *,
    texto_doc: str,
    marcador_inicio: str,
    marcador_fin: str,
    nombre_bloque: str,
) -> tuple[str, ...]:
    lineas = texto_doc.splitlines()
    lineas_normalizadas = [linea.strip() for linea in lineas]
    try:
        inicio = lineas_normalizadas.index(marcador_inicio)
    except ValueError as exc:
        raise ErrorContratoReasonCodesDoc(f"No se encontró marcador de inicio de {nombre_bloque}: {marcador_inicio}") from exc
    try:
        fin = lineas_normalizadas.index(marcador_fin)
    except ValueError as exc:
        raise ErrorContratoReasonCodesDoc(f"No se encontró marcador de cierre de {nombre_bloque}: {marcador_fin}") from exc
    if fin <= inicio + 1:
        raise ErrorContratoReasonCodesDoc(
            f"Bloque de {nombre_bloque} vacío o delimitación inválida entre marcadores START/END."
        )
    return tuple(lineas[inicio + 1 : fin])
