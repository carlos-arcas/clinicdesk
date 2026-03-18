# Arquitectura C4 (ClinicDesk)

Este documento resume la arquitectura con diagramas C4 en Mermaid, usando módulos reales del repositorio.

## 1) Context Diagram

```mermaid
flowchart LR
    recepcion[Recepción / Operación clínica]
    coordinacion[Coordinación médica]
    analista[Analista de negocio / BI]
    admin[Administrador técnico]

    clinicdesk[ClinicDesk]
    pbi[Power BI]

    recepcion -->|Gestiona citas y confirmaciones| clinicdesk
    coordinacion -->|Supervisa agenda y riesgo| clinicdesk
    admin -->|Configura entorno y quality gate| clinicdesk
    clinicdesk -->|CSV de métricas/scoring/drift| pbi
    analista -->|Consume dashboards| pbi
```

## 2) Container Diagram

```mermaid
flowchart TB
    subgraph sistema[ClinicDesk]
        ui[Presentación\nPySide6 UI + CLI scripts]
        app[Aplicación\nUse cases + services + ports]
        domain[Dominio\nEntidades y reglas de negocio]
        infra[Infraestructura\nRepositorios SQLite/JSON + adapters]
    end

    sqlite[(SQLite\n./data/clinicdesk.db)]
    fs[(Filesystem\nfeature_store / model_store / exports)]

    ui --> app
    app --> domain
    app --> infra
    infra --> sqlite
    infra --> fs
```

## 3) Component Diagram (ejemplo acotado)

```mermaid
flowchart LR
    subgraph presentacion[Presentación]
                pageCitas[pages/citas/page.py]
    end

    subgraph aplicacion[Aplicación]
        facadeDemo[services/DemoMLFacade]
        ucCitas[application/citas/usecases.py]
        auditService[application/auditoria/audit_service.py]
        prefsService[application/preferencias/preferencias_usuario.py]
    end

    subgraph infraestructura[Infraestructura]
        repoSqlite[infrastructure/sqlite/*]
        repoPrefs[infrastructure/preferencias/*]
        outJson[infrastructure/json_*]
    end

    subgraph dominio[Dominio]
        domCitas[domain/citas.py]
        domPersonas[domain/personas.py]
    end

    pageCitas --> ucCitas
    facadeDemo --> ucCitas
    ucCitas --> domCitas
    ucCitas --> domPersonas
    facadeDemo --> repoSqlite
    auditService --> repoSqlite
    prefsService --> repoPrefs
    facadeDemo --> outJson
```

> Nota: el diagrama de componentes es intencionalmente breve y orientado a lectura rápida del producto.
