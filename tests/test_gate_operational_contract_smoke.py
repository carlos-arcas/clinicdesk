from __future__ import annotations

from types import SimpleNamespace

from scripts import gate_pr
from scripts import gate_rapido
from scripts.quality_gate_components import bloqueo_operativo
from scripts.quality_gate_components.contrato_reason_codes_doc import cargar_snippets_semantica_bloqueo_operativo
from scripts.quality_gate_components.ejecucion_canonica import DecisionEjecucionCanonica


class _Interprete:
    usa_python_repo = True


class _DiagnosticoBloqueado:
    toolchain_error = None
    herramientas = ()
    wheelhouse_disponible = False
    wheelhouse = None
    python_activo = "3.12.0"
    python_path = "/tmp/python"
    venv_activo = False
    cache_pip = None
    indice_pip = None
    proxy_configurado = False
    diagnostico_red = "sin wheelhouse"
    source_of_truth = "requirements-dev.txt"
    tiene_faltantes = True
    tiene_desalineaciones = False
    entorno_bloqueado = True
    interprete = _Interprete()


def _parches_bloqueo_operativo(monkeypatch) -> None:
    monkeypatch.setattr(
        bloqueo_operativo,
        "clasificar_bloqueo_entorno",
        lambda _diag: SimpleNamespace(
            reason_code="DEPENDENCIAS_FALTANTES",
            categoria="toolchain",
            detalle="Faltan herramientas del gate en el intérprete activo.",
            accion_sugerida="python -m pip install -r requirements-dev.txt",
        ),
    )
    monkeypatch.setattr(
        bloqueo_operativo,
        "renderizar_reporte",
        lambda _diag: ["[doctor][reason_code] DEPENDENCIAS_FALTANTES"],
    )


def _assert_contrato_bloqueo_operativo(
    stderr: str,
    etiqueta_gate: str,
    snippets_semantica: tuple[str, ...],
) -> None:
    assert f"[{etiqueta_gate}][entorno] rc=20" in stderr
    for snippet in snippets_semantica:
        assert snippet in stderr


def test_smoke_transversal_contrato_operativo_compartido(monkeypatch, capsys) -> None:
    _parches_bloqueo_operativo(monkeypatch)
    snippets_semantica = cargar_snippets_semantica_bloqueo_operativo(gate_pr.RUTA_DOC_CI_QUALITY_GATE)

    monkeypatch.setattr(gate_pr, "resolver_ejecucion_canonica", lambda *_args, **_kwargs: DecisionEjecucionCanonica("continuar"))
    monkeypatch.setattr(gate_pr, "diagnosticar_entorno_calidad", lambda _root: _DiagnosticoBloqueado())
    monkeypatch.setattr(gate_pr, "codigo_salida_estable", lambda _diag: 2)
    monkeypatch.setattr(
        gate_pr.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("gate_pr no debe ejecutar validación funcional")),
    )

    monkeypatch.setattr(gate_rapido, "resolver_ejecucion_canonica", lambda *_args, **_kwargs: DecisionEjecucionCanonica("continuar"))
    monkeypatch.setattr(gate_rapido, "diagnosticar_entorno_calidad", lambda _root: _DiagnosticoBloqueado())
    monkeypatch.setattr(gate_rapido, "codigo_salida_estable", lambda _diag: 2)
    monkeypatch.setattr(
        gate_rapido.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("gate_rapido no debe ejecutar validación funcional")
        ),
    )

    rc_pr = gate_pr.main()
    err_pr = capsys.readouterr().err

    rc_rapido = gate_rapido.main()
    err_rapido = capsys.readouterr().err

    assert rc_pr == gate_pr.EXIT_ENTORNO_BLOQUEADO == 20
    assert rc_rapido == gate_rapido.EXIT_ENTORNO_BLOQUEADO == 20
    _assert_contrato_bloqueo_operativo(err_pr, "gate-pr", snippets_semantica)
    _assert_contrato_bloqueo_operativo(err_rapido, "gate-rapido", snippets_semantica)
