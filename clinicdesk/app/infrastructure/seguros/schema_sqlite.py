from __future__ import annotations

import sqlite3


def inicializar_schema_comercial_seguro(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS seguro_oportunidades (
            id_oportunidad TEXT PRIMARY KEY,
            id_candidato TEXT NOT NULL,
            id_paciente TEXT NOT NULL,
            segmento TEXT NOT NULL,
            plan_origen_id TEXT NOT NULL,
            plan_destino_id TEXT NOT NULL,
            estado_actual TEXT NOT NULL,
            clasificacion_motor TEXT NOT NULL,
            segmento_cliente TEXT,
            origen_cliente TEXT,
            necesidad_principal TEXT,
            motivaciones_json TEXT,
            objecion_principal TEXT,
            sensibilidad_precio TEXT,
            friccion_migracion TEXT,
            fit_comercial TEXT,
            fit_motivo TEXT,
            fit_riesgos_json TEXT,
            fit_argumentos_json TEXT,
            fit_conviene_insistir INTEGER,
            fit_revision_humana INTEGER,
            resultado_comercial TEXT,
            creado_en TEXT NOT NULL,
            actualizado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seguro_seguimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oportunidad TEXT NOT NULL,
            fecha_registro TEXT NOT NULL,
            estado TEXT NOT NULL,
            accion_comercial TEXT NOT NULL,
            nota_corta TEXT NOT NULL,
            siguiente_paso TEXT NOT NULL,
            FOREIGN KEY (id_oportunidad) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_ofertas (
            id_oferta TEXT PRIMARY KEY,
            id_oportunidad TEXT NOT NULL UNIQUE,
            plan_propuesto_id TEXT NOT NULL,
            resumen_valor TEXT NOT NULL,
            puntos_fuertes_json TEXT NOT NULL,
            riesgos_revision_json TEXT NOT NULL,
            clasificacion_migracion TEXT NOT NULL,
            notas_comerciales_json TEXT NOT NULL,
            creada_en TEXT NOT NULL,
            actualizada_en TEXT NOT NULL,
            FOREIGN KEY (id_oportunidad) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_renovaciones (
            id_renovacion TEXT PRIMARY KEY,
            id_oportunidad TEXT NOT NULL UNIQUE,
            plan_vigente_id TEXT NOT NULL,
            fecha_renovacion TEXT NOT NULL,
            revision_pendiente INTEGER NOT NULL,
            resultado TEXT NOT NULL,
            actualizada_en TEXT NOT NULL,
            FOREIGN KEY (id_oportunidad) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_gestiones_operativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_oportunidad TEXT NOT NULL,
            accion TEXT NOT NULL,
            estado_resultante TEXT NOT NULL,
            nota_corta TEXT NOT NULL,
            siguiente_paso TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (id_oportunidad) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_estado ON seguro_oportunidades (estado_actual);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_plan_destino ON seguro_oportunidades (plan_destino_id);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_clasificacion ON seguro_oportunidades (clasificacion_motor);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_segmento ON seguro_oportunidades (segmento_cliente);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_fit ON seguro_oportunidades (fit_comercial);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_objecion ON seguro_oportunidades (objecion_principal);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_sensibilidad ON seguro_oportunidades (sensibilidad_precio);
        CREATE INDEX IF NOT EXISTS idx_seguro_oportunidades_actualizado ON seguro_oportunidades (actualizado_en);
        CREATE INDEX IF NOT EXISTS idx_seguro_seguimientos_oportunidad_fecha
            ON seguro_seguimientos (id_oportunidad, fecha_registro DESC);
        CREATE INDEX IF NOT EXISTS idx_seguro_gestiones_operativas_oportunidad_fecha
            ON seguro_gestiones_operativas (id_oportunidad, timestamp DESC);
        """
    )
    connection.commit()
