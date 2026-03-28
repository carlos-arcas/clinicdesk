# Auditoría SEO — Proyecto Narrativa-SEO (Prompt 2)

## Resultado de inspección de alcance solicitado

Se verificó el árbol real del repositorio en `/workspace/clinicdesk` y **no existen** las rutas objetivo del prompt:

- `frontend/app/biblioteca/page.tsx`
- `frontend/app/biblioteca/[tipo]/[id]/page.tsx`
- helpers SEO de Next.js (`generateMetadata`, `sitemap.ts`, `robots.ts`, etc.)

Adicionalmente, no se detectó carpeta `frontend/` ni archivos `.tsx` tipo App Router.

## Hallazgos estructurales

El repositorio actual es una aplicación Python (Clean Architecture) con:

- capa web API en `clinicdesk/web/`
- templates en `presentacion/webapp/templates/`
- sin rutas públicas tipo `/biblioteca` en stack Next.js

## Impacto en el objetivo del prompt

Con el contenido disponible en esta rama/repo no es posible implementar cambios solicitados de:

- metadata dinámica por página en Next.js
- sitemap dinámico de `/biblioteca` y `/biblioteca/[tipo]/[id]`
- canonicals por detalle en App Router
- JSON-LD por detalle en páginas `.tsx`

## Próximo paso técnico requerido

Para ejecutar el prompt 2 tal como fue definido, se requiere el repositorio/paquete correcto que contenga el frontend Next.js con las rutas de biblioteca.
