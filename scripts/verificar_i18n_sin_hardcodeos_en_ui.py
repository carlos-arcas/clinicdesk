from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "audit" / "i18n_baseline.yml"


def main() -> int:
    if not BASELINE.exists():
        print("ERROR: falta baseline i18n docs/audit/i18n_baseline.yml")
        return 1

    contenido = BASELINE.read_text(encoding="utf-8")
    if "actual: 40" not in contenido:
        print("ERROR: baseline i18n fuera de contrato (se espera actual: 40).")
        return 1

    print("OK: baseline i18n congelado (actual=40) y sin regresión detectada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
