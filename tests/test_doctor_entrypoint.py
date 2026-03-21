from __future__ import annotations

from scripts import doctor_entorno_calidad
from scripts.quality_gate_components.ejecucion_canonica import DecisionEjecucionCanonica


def test_doctor_reejecuta_en_python_del_repo(monkeypatch) -> None:
    observado: dict[str, object] = {}
    monkeypatch.setattr(
        doctor_entorno_calidad,
        "resolver_ejecucion_canonica",
        lambda *_args, **_kwargs: DecisionEjecucionCanonica("reejecutar", python_objetivo=doctor_entorno_calidad.REPO_ROOT / ".venv" / "bin" / "python"),
    )
    monkeypatch.setattr(
        doctor_entorno_calidad,
        "reejecutar_en_python_objetivo",
        lambda decision, argv: observado.update({"decision": decision, "argv": argv}) or 6,
    )

    rc = doctor_entorno_calidad.main()

    assert rc == 6
    assert observado["argv"][:2] == ["-m", "scripts.doctor_entorno_calidad"]


def test_doctor_bloquea_si_falta_venv_repo(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        doctor_entorno_calidad,
        "resolver_ejecucion_canonica",
        lambda *_args, **_kwargs: DecisionEjecucionCanonica("bloquear", mensaje=("[canonico][error] falta .venv",)),
    )

    rc = doctor_entorno_calidad.main()

    assert rc == 1
    assert "falta .venv" in capsys.readouterr().err
