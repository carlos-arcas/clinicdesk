# Análisis de brecha: feature "Notificaciones internas + unread count en chat (MVP)"

## Resumen

Se revisó el repositorio actual para ubicar la base técnica requerida por la feature solicitada (chat 1:1, muro social, seguimientos, bloqueos y API HTTP de notificaciones). El resultado es que el código activo del proyecto corresponde a una aplicación de gestión clínica/ML con arquitectura Clean en `clinicdesk/app/*`, sin backend Django REST ni módulos de dominio para red social en producción.

## Hallazgos

1. No existe proyecto Django con `settings.py`, `urls.py`, `models.py` y `views.py` para endpoints API.
2. No existen módulos actuales de `conversaciones`, `mensajes privados`, `seguimientos` o `bloqueos` en el backend.
3. El único rastro web es un conjunto mínimo de plantillas en `presentacion/webapp/templates/webapp/` sin capa de dominio/aplicación asociada.
4. El README describe una solución de analítica y predicción clínica (ML), no una red social.

## Impacto

Implementar la feature pedida de forma correcta y retrocompatible requiere primero introducir una base de backend web inexistente en este repositorio (modelo de usuarios web, API auth, ORM de chat/muro, puertos, casos de uso y test stack web). Sin esa base, no es técnicamente viable entregar el alcance funcional solicitado con garantías de arquitectura y cobertura.

## Propuesta técnica mínima para habilitar la feature en este repo

1. Definir bounded context social en `clinicdesk/app` (dominio/aplicación/infra/presentación) antes de endpoints.
2. Elegir framework HTTP oficial para el repositorio (Django/Flask/FastAPI) y fijar contrato en `docs/decisiones/*`.
3. Implementar en fases:
   - Fase 1: entidades/puertos/casos de uso + repositorios fake y tests core.
   - Fase 2: persistencia ORM + migraciones + anti N+1.
   - Fase 3: endpoints + auth + i18n + hardening + tests e2e.
4. Integrar `python -m scripts.gate_pr` con los nuevos checks web solo cuando la base esté estable.

## Estado

- Feature de notificaciones/chat: **BLOQUEADA por incompatibilidad de alcance con la base actual del repositorio**.
- Se recomienda alinear primero el contexto funcional esperado del repositorio o facilitar el repositorio correcto donde existen los módulos sociales mencionados.
