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



        CREATE TABLE IF NOT EXISTS seguro_campanias (
            id_campania TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            objetivo_comercial TEXT NOT NULL,
            origen TEXT NOT NULL,
            criterio_descripcion TEXT NOT NULL,
            criterio_referencia TEXT,
            creado_en TEXT NOT NULL,
            tamano_lote INTEGER NOT NULL,
            estado TEXT NOT NULL,
            total_items INTEGER NOT NULL,
            trabajados INTEGER NOT NULL,
            convertidos INTEGER NOT NULL,
            rechazados INTEGER NOT NULL,
            pendientes INTEGER NOT NULL,
            ratio_conversion REAL NOT NULL,
            ratio_avance REAL NOT NULL,
            actualizado_en TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS seguro_campania_items (
            id_item TEXT PRIMARY KEY,
            id_campania TEXT NOT NULL,
            id_oportunidad TEXT NOT NULL,
            estado_trabajo TEXT NOT NULL,
            accion_tomada TEXT NOT NULL,
            resultado TEXT NOT NULL,
            nota_corta TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (id_campania) REFERENCES seguro_campanias(id_campania) ON DELETE CASCADE,
            FOREIGN KEY (id_oportunidad) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS seguro_polizas (
            id_poliza TEXT PRIMARY KEY,
            id_oportunidad_origen TEXT NOT NULL,
            id_paciente TEXT NOT NULL,
            id_plan TEXT NOT NULL,
            estado_poliza TEXT NOT NULL,
            titular_id_asegurado TEXT NOT NULL,
            titular_nombre TEXT NOT NULL,
            titular_documento TEXT NOT NULL,
            titular_estado TEXT NOT NULL,
            vigencia_inicio TEXT NOT NULL,
            vigencia_fin TEXT NOT NULL,
            renovacion_fecha TEXT NOT NULL,
            renovacion_estado TEXT NOT NULL,
            coberturas_json TEXT NOT NULL,
            actualizado_en TEXT NOT NULL,
            FOREIGN KEY (id_oportunidad_origen) REFERENCES seguro_oportunidades(id_oportunidad) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS seguro_poliza_beneficiarios (
            id_beneficiario TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            nombre TEXT NOT NULL,
            parentesco TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_poliza_incidencias (
            id_incidencia TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_apertura TEXT NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE
        );



        CREATE TABLE IF NOT EXISTS seguro_poliza_cuotas (
            id_cuota TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            periodo TEXT NOT NULL,
            fecha_emision TEXT NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            importe REAL NOT NULL,
            estado_cuota TEXT NOT NULL,
            fecha_pago TEXT,
            actualizado_en TEXT NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_poliza_impagos (
            id_evento TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            id_cuota TEXT NOT NULL,
            fecha_evento TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE,
            FOREIGN KEY (id_cuota) REFERENCES seguro_poliza_cuotas(id_cuota) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_poliza_suspensiones (
            id_evento TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            fecha_evento TEXT NOT NULL,
            motivo TEXT NOT NULL,
            automatica INTEGER NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS seguro_poliza_reactivaciones (
            id_evento TEXT PRIMARY KEY,
            id_poliza TEXT NOT NULL,
            fecha_evento TEXT NOT NULL,
            motivo TEXT NOT NULL,
            FOREIGN KEY (id_poliza) REFERENCES seguro_polizas(id_poliza) ON DELETE CASCADE
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

        CREATE INDEX IF NOT EXISTS idx_seguro_polizas_estado ON seguro_polizas (estado_poliza);
        CREATE INDEX IF NOT EXISTS idx_seguro_polizas_plan ON seguro_polizas (id_plan);
        CREATE INDEX IF NOT EXISTS idx_seguro_polizas_vigencia_fin ON seguro_polizas (vigencia_fin);
        CREATE INDEX IF NOT EXISTS idx_seguro_polizas_renovacion ON seguro_polizas (renovacion_estado);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_beneficiarios_poliza ON seguro_poliza_beneficiarios (id_poliza);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_incidencias_poliza_fecha
            ON seguro_poliza_incidencias (id_poliza, fecha_apertura DESC);

        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_cuotas_poliza_vencimiento
            ON seguro_poliza_cuotas (id_poliza, fecha_vencimiento ASC);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_cuotas_estado
            ON seguro_poliza_cuotas (estado_cuota);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_impagos_poliza_fecha
            ON seguro_poliza_impagos (id_poliza, fecha_evento DESC);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_suspensiones_poliza_fecha
            ON seguro_poliza_suspensiones (id_poliza, fecha_evento DESC);
        CREATE INDEX IF NOT EXISTS idx_seguro_poliza_reactivaciones_poliza_fecha
            ON seguro_poliza_reactivaciones (id_poliza, fecha_evento DESC);


        CREATE INDEX IF NOT EXISTS idx_seguro_campanias_estado ON seguro_campanias (estado);
        CREATE INDEX IF NOT EXISTS idx_seguro_campania_items_campania ON seguro_campania_items (id_campania, timestamp DESC);
        """
    )
    connection.commit()
