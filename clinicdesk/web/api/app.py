from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request

from clinicdesk.web.api.router_api import get_servicio_api, router
from clinicdesk.web.api.servicio_consultas import ServicioConsultasApi, construir_servicio_consultas


def create_app(servicio: ServicioConsultasApi | None = None) -> FastAPI:
    app = FastAPI(title="ClinicDesk API", version="1.0.0")
    servicio_api = servicio or construir_servicio_consultas()

    app.dependency_overrides[get_servicio_api] = lambda: servicio_api

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app


app = create_app()
