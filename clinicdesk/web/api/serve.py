from __future__ import annotations

import os

import uvicorn


def main() -> int:
    puerto = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("clinicdesk.web.api.app:app", host="0.0.0.0", port=puerto)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
