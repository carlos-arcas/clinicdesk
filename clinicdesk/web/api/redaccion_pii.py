from __future__ import annotations

from clinicdesk.app.application.seguridad_salida import (
    redactar_email_visible as redactar_email,
)
from clinicdesk.app.application.seguridad_salida import (
    redactar_telefono_visible as redactar_telefono,
)
from clinicdesk.app.application.seguridad_salida import redactar_texto_visible as redactar_texto

__all__ = ["redactar_texto", "redactar_email", "redactar_telefono"]
