-- infrastructure/sqlite/schema.sql
PRAGMA foreign_keys = ON;

-- ============================================================
-- PERSONAS (tablas separadas; no existe "personas")
-- ============================================================

CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT NOT NULL,
    documento TEXT NOT NULL,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    fecha_nacimiento TEXT, -- ISO date: YYYY-MM-DD
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,

    num_historia TEXT,
    alergias TEXT,
    observaciones TEXT,

    UNIQUE (tipo_documento, documento)
);

CREATE INDEX IF NOT EXISTS idx_pacientes_nombre_apellidos ON pacientes(nombre, apellidos);
CREATE INDEX IF NOT EXISTS idx_pacientes_documento ON pacientes(documento);


CREATE TABLE IF NOT EXISTS medicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT NOT NULL,
    documento TEXT NOT NULL,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    fecha_nacimiento TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,

    num_colegiado TEXT NOT NULL,
    especialidad TEXT NOT NULL,

    UNIQUE (tipo_documento, documento),
    UNIQUE (num_colegiado)
);

CREATE INDEX IF NOT EXISTS idx_medicos_nombre_apellidos ON medicos(nombre, apellidos);
CREATE INDEX IF NOT EXISTS idx_medicos_especialidad ON medicos(especialidad);


CREATE TABLE IF NOT EXISTS personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_documento TEXT NOT NULL,
    documento TEXT NOT NULL,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    telefono TEXT,
    email TEXT,
    fecha_nacimiento TEXT,
    direccion TEXT,
    activo INTEGER NOT NULL DEFAULT 1,

    puesto TEXT NOT NULL,
    turno TEXT,

    UNIQUE (tipo_documento, documento)
);

CREATE INDEX IF NOT EXISTS idx_personal_nombre_apellidos ON personal(nombre, apellidos);
CREATE INDEX IF NOT EXISTS idx_personal_puesto ON personal(puesto);

-- ============================================================
-- SALAS
-- ============================================================

CREATE TABLE IF NOT EXISTS salas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    ubicacion TEXT,
    activa INTEGER NOT NULL DEFAULT 1,

    UNIQUE (nombre)
);

CREATE INDEX IF NOT EXISTS idx_salas_tipo ON salas(tipo);

-- ============================================================
-- TURNOS / CUADRANTES (calendarios editables)
-- ============================================================

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    hora_inicio TEXT NOT NULL, -- "HH:MM"
    hora_fin TEXT NOT NULL,    -- "HH:MM"
    activo INTEGER NOT NULL DEFAULT 1,

    UNIQUE (nombre)
);

-- Bloques de trabajo por día (médicos)
CREATE TABLE IF NOT EXISTS calendario_medico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medico_id INTEGER NOT NULL,
    fecha TEXT NOT NULL, -- YYYY-MM-DD
    turno_id INTEGER NOT NULL,

    hora_inicio_override TEXT, -- "HH:MM" opcional
    hora_fin_override TEXT,    -- "HH:MM" opcional
    observaciones TEXT,
    activo INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE RESTRICT,
    FOREIGN KEY (turno_id) REFERENCES turnos(id) ON DELETE RESTRICT,

    UNIQUE (medico_id, fecha, turno_id)
);

CREATE INDEX IF NOT EXISTS idx_cal_med_medico_fecha ON calendario_medico(medico_id, fecha);
CREATE INDEX IF NOT EXISTS idx_cal_med_fecha ON calendario_medico(fecha);

-- Bloques de trabajo por día (personal)
CREATE TABLE IF NOT EXISTS calendario_personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_id INTEGER NOT NULL,
    fecha TEXT NOT NULL, -- YYYY-MM-DD
    turno_id INTEGER NOT NULL,

    hora_inicio_override TEXT,
    hora_fin_override TEXT,
    observaciones TEXT,
    activo INTEGER NOT NULL DEFAULT 1,

    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE RESTRICT,
    FOREIGN KEY (turno_id) REFERENCES turnos(id) ON DELETE RESTRICT,

    UNIQUE (personal_id, fecha, turno_id)
);

CREATE INDEX IF NOT EXISTS idx_cal_per_personal_fecha ON calendario_personal(personal_id, fecha);
CREATE INDEX IF NOT EXISTS idx_cal_per_fecha ON calendario_personal(fecha);

-- Ausencias (médicos)
CREATE TABLE IF NOT EXISTS ausencias_medico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medico_id INTEGER NOT NULL,

    inicio TEXT NOT NULL, -- ISO datetime "YYYY-MM-DD HH:MM:SS" o date "YYYY-MM-DD"
    fin TEXT NOT NULL,    -- ISO datetime o date

    tipo TEXT NOT NULL,   -- VACACIONES/BAJA/PERMISO/...
    motivo TEXT,
    aprobado_por_personal_id INTEGER,
    creado_en TEXT NOT NULL,

    FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE RESTRICT,
    FOREIGN KEY (aprobado_por_personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_aus_med_medico_inicio ON ausencias_medico(medico_id, inicio);
CREATE INDEX IF NOT EXISTS idx_aus_med_medico_fin ON ausencias_medico(medico_id, fin);

-- Ausencias (personal)
CREATE TABLE IF NOT EXISTS ausencias_personal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    personal_id INTEGER NOT NULL,

    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,

    tipo TEXT NOT NULL,
    motivo TEXT,
    aprobado_por_personal_id INTEGER,
    creado_en TEXT NOT NULL,

    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE RESTRICT,
    FOREIGN KEY (aprobado_por_personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_aus_per_personal_inicio ON ausencias_personal(personal_id, inicio);
CREATE INDEX IF NOT EXISTS idx_aus_per_personal_fin ON ausencias_personal(personal_id, fin);

-- ============================================================
-- CITAS (con override consciente)
-- ============================================================

CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    medico_id INTEGER NOT NULL,
    sala_id INTEGER NOT NULL,

    inicio TEXT NOT NULL, -- ISO datetime
    fin TEXT NOT NULL,    -- ISO datetime
    estado TEXT NOT NULL,
    motivo TEXT,
    notas TEXT,

    override_ok INTEGER NOT NULL DEFAULT 0,
    override_nota TEXT,
    override_personal_id INTEGER,
    override_fecha_hora TEXT,

    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE RESTRICT,
    FOREIGN KEY (sala_id) REFERENCES salas(id) ON DELETE RESTRICT,
    FOREIGN KEY (override_personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_citas_inicio ON citas(inicio);
CREATE INDEX IF NOT EXISTS idx_citas_medico_inicio ON citas(medico_id, inicio);
CREATE INDEX IF NOT EXISTS idx_citas_sala_inicio ON citas(sala_id, inicio);
CREATE INDEX IF NOT EXISTS idx_citas_paciente_inicio ON citas(paciente_id, inicio);

-- ============================================================
-- INVENTARIO (tablas separadas)
-- ============================================================

CREATE TABLE IF NOT EXISTS medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_compuesto TEXT NOT NULL,
    nombre_comercial TEXT NOT NULL,
    cantidad_almacen INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_meds_compuesto ON medicamentos(nombre_compuesto);
CREATE INDEX IF NOT EXISTS idx_meds_comercial ON medicamentos(nombre_comercial);


CREATE TABLE IF NOT EXISTS materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    fungible INTEGER NOT NULL DEFAULT 1,
    cantidad_almacen INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_material_nombre ON materiales(nombre);

-- ============================================================
-- RECETAS (auditoría)
-- ============================================================

CREATE TABLE IF NOT EXISTS recetas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER NOT NULL,
    medico_id INTEGER NOT NULL,
    fecha TEXT NOT NULL, -- ISO datetime
    observaciones TEXT,

    FOREIGN KEY (paciente_id) REFERENCES pacientes(id) ON DELETE RESTRICT,
    FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_recetas_paciente_fecha ON recetas(paciente_id, fecha);
CREATE INDEX IF NOT EXISTS idx_recetas_medico_fecha ON recetas(medico_id, fecha);


CREATE TABLE IF NOT EXISTS receta_lineas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receta_id INTEGER NOT NULL,
    medicamento_id INTEGER NOT NULL,

    dosis TEXT NOT NULL,
    duracion_dias INTEGER,
    instrucciones TEXT,

    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE CASCADE,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_receta_lineas_receta ON receta_lineas(receta_id);
CREATE INDEX IF NOT EXISTS idx_receta_lineas_medicamento ON receta_lineas(medicamento_id);

-- ============================================================
-- DISPENSACIONES (auditoría + vínculo a receta)
-- ============================================================

CREATE TABLE IF NOT EXISTS dispensaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    receta_id INTEGER NOT NULL,
    receta_linea_id INTEGER, -- opcional

    medicamento_id INTEGER NOT NULL,
    personal_id INTEGER NOT NULL,

    fecha_hora TEXT NOT NULL, -- ISO datetime
    cantidad INTEGER NOT NULL,
    observaciones TEXT,

    override_ok INTEGER NOT NULL DEFAULT 0,
    override_nota TEXT,
    override_personal_id INTEGER,
    override_fecha_hora TEXT,

    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE RESTRICT,
    FOREIGN KEY (receta_linea_id) REFERENCES receta_lineas(id) ON DELETE SET NULL,
    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE RESTRICT,
    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE RESTRICT,
    FOREIGN KEY (override_personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_disp_receta ON dispensaciones(receta_id);
CREATE INDEX IF NOT EXISTS idx_disp_personal_fecha ON dispensaciones(personal_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_disp_medicamento_fecha ON dispensaciones(medicamento_id, fecha_hora);

-- ============================================================
-- MOVIMIENTOS (auditoría separada)
-- ============================================================

CREATE TABLE IF NOT EXISTS movimientos_medicamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicamento_id INTEGER NOT NULL,

    fecha_hora TEXT NOT NULL, -- ISO datetime
    tipo TEXT NOT NULL,       -- ENTRADA / SALIDA / AJUSTE
    cantidad INTEGER NOT NULL,
    motivo TEXT,

    receta_id INTEGER,
    dispensacion_id INTEGER,
    personal_id INTEGER,

    FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE RESTRICT,
    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE SET NULL,
    FOREIGN KEY (dispensacion_id) REFERENCES dispensaciones(id) ON DELETE SET NULL,
    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_mov_med_medicamento_fecha ON movimientos_medicamentos(medicamento_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_mov_med_personal_fecha ON movimientos_medicamentos(personal_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_mov_med_receta ON movimientos_medicamentos(receta_id);
CREATE INDEX IF NOT EXISTS idx_mov_med_disp ON movimientos_medicamentos(dispensacion_id);


CREATE TABLE IF NOT EXISTS movimientos_materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL,

    fecha_hora TEXT NOT NULL,
    tipo TEXT NOT NULL,
    cantidad INTEGER NOT NULL,
    motivo TEXT,

    personal_id INTEGER,

    FOREIGN KEY (material_id) REFERENCES materiales(id) ON DELETE RESTRICT,
    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_mov_mat_material_fecha ON movimientos_materiales(material_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_mov_mat_personal_fecha ON movimientos_materiales(personal_id, fecha_hora);

-- ============================================================
-- INCIDENCIAS (solo cuando hay override consciente)
-- ============================================================

CREATE TABLE IF NOT EXISTS incidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tipo TEXT NOT NULL,
    severidad TEXT NOT NULL,
    estado TEXT NOT NULL,

    fecha_hora TEXT NOT NULL, -- ISO datetime
    descripcion TEXT NOT NULL,

    medico_id INTEGER,
    personal_id INTEGER,

    cita_id INTEGER,
    dispensacion_id INTEGER,
    receta_id INTEGER,

    confirmado_por_personal_id INTEGER NOT NULL,
    nota_override TEXT NOT NULL,

    FOREIGN KEY (medico_id) REFERENCES medicos(id) ON DELETE SET NULL,
    FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE SET NULL,
    FOREIGN KEY (cita_id) REFERENCES citas(id) ON DELETE SET NULL,
    FOREIGN KEY (dispensacion_id) REFERENCES dispensaciones(id) ON DELETE SET NULL,
    FOREIGN KEY (receta_id) REFERENCES recetas(id) ON DELETE SET NULL,
    FOREIGN KEY (confirmado_por_personal_id) REFERENCES personal(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_incidencias_fecha ON incidencias(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_incidencias_tipo_estado ON incidencias(tipo, estado);
CREATE INDEX IF NOT EXISTS idx_incidencias_medico_fecha ON incidencias(medico_id, fecha_hora);
CREATE INDEX IF NOT EXISTS idx_incidencias_personal_fecha ON incidencias(personal_id, fecha_hora);
