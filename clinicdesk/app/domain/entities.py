"""Entidades de dominio."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Dict, Optional

from clinicdesk.app.domain.enums import (
    EstadoCita,
    EstadoIncidencia,
    SeveridadIncidencia,
    TipoDocumento,
    TipoIncidencia,
    TipoMovimientoStock,
    TipoSala,
)
from clinicdesk.app.domain.exceptions import ValidationError
from clinicdesk.app.domain.value_objects import (
    _ensure_non_negative,
    _ensure_positive_id,
    _require_non_empty,
    _require_override_note,
    _strip_or_none,
    _validate_email_basic,
    _validate_phone_basic,
)


@dataclass(slots=True)
class Persona:
    """Clase base para personas del dominio (no tiene tabla SQL propia)."""

    id: Optional[int] = None
    tipo_documento: TipoDocumento = TipoDocumento.DNI
    documento: str = ""
    nombre: str = ""
    apellidos: str = ""
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    direccion: Optional[str] = None
    activo: bool = True

    def validar(self) -> None:
        """Invariantes comunes para cualquier persona."""
        self.documento = _require_non_empty(self.documento, "documento")
        self.nombre = _require_non_empty(self.nombre, "nombre")
        self.apellidos = _require_non_empty(self.apellidos, "apellidos")

        self.telefono = _strip_or_none(self.telefono)
        self.email = _strip_or_none(self.email)
        self.direccion = _strip_or_none(self.direccion)

        _validate_phone_basic(self.telefono)
        _validate_email_basic(self.email)

    def nombre_completo(self) -> str:
        """Nombre completo para listados o documentos."""
        return f"{self.nombre} {self.apellidos}".strip()

    def to_dict(self) -> Dict[str, Any]:
        """Serialización básica a dict (útil para CSV/JSON)."""
        d = asdict(self)
        d["tipo_documento"] = self.tipo_documento.value
        if self.fecha_nacimiento is not None:
            d["fecha_nacimiento"] = self.fecha_nacimiento.isoformat()
        return d


@dataclass(slots=True)
class Paciente(Persona):
    """Paciente (tabla SQL: pacientes)."""

    num_historia: Optional[str] = None
    alergias: Optional[str] = None
    observaciones: Optional[str] = None

    def validar(self) -> None:
        super(Paciente, self).validar()
        self.num_historia = _strip_or_none(self.num_historia)
        self.alergias = _strip_or_none(self.alergias)
        self.observaciones = _strip_or_none(self.observaciones)


@dataclass(slots=True)
class Medico(Persona):
    """Médico (tabla SQL: medicos)."""

    num_colegiado: str = ""
    especialidad: str = ""

    def validar(self) -> None:
        super(Medico, self).validar()
        self.num_colegiado = _require_non_empty(self.num_colegiado, "num_colegiado")
        self.especialidad = _require_non_empty(self.especialidad, "especialidad")


@dataclass(slots=True)
class Personal(Persona):
    """Personal (tabla SQL: personal)."""

    puesto: str = ""
    turno: Optional[str] = None

    def validar(self) -> None:
        super(Personal, self).validar()
        self.puesto = _require_non_empty(self.puesto, "puesto")
        self.turno = _strip_or_none(self.turno)


@dataclass(slots=True)
class Sala:
    """Sala de la clínica (tabla SQL: salas)."""

    id: Optional[int] = None
    nombre: str = ""
    tipo: TipoSala = TipoSala.CONSULTA
    ubicacion: Optional[str] = None
    activa: bool = True

    def validar(self) -> None:
        self.nombre = _require_non_empty(self.nombre, "nombre")
        self.ubicacion = _strip_or_none(self.ubicacion)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        return d


@dataclass(slots=True)
class Medicamento:
    """Medicamento (tabla SQL: medicamentos)."""

    id: Optional[int] = None
    nombre_compuesto: str = ""
    nombre_comercial: str = ""
    cantidad_almacen: int = 0
    activo: bool = True

    def validar(self) -> None:
        self.nombre_compuesto = _require_non_empty(self.nombre_compuesto, "nombre_compuesto")
        self.nombre_comercial = _require_non_empty(self.nombre_comercial, "nombre_comercial")
        _ensure_non_negative(self.cantidad_almacen, "cantidad_almacen")

    def nombre_para_listado(self) -> str:
        return f"{self.nombre_comercial} ({self.nombre_compuesto})"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def cantidad_en_almacen(self) -> int:
        return self.cantidad_almacen

    @cantidad_en_almacen.setter
    def cantidad_en_almacen(self, value: int) -> None:
        self.cantidad_almacen = value


@dataclass(slots=True)
class Material:
    """Material (tabla SQL: materiales)."""

    id: Optional[int] = None
    nombre: str = ""
    fungible: bool = True
    cantidad_almacen: int = 0
    activo: bool = True

    def validar(self) -> None:
        self.nombre = _require_non_empty(self.nombre, "nombre")
        _ensure_non_negative(self.cantidad_almacen, "cantidad_almacen")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def cantidad_en_almacen(self) -> int:
        return self.cantidad_almacen

    @cantidad_en_almacen.setter
    def cantidad_en_almacen(self, value: int) -> None:
        self.cantidad_almacen = value


@dataclass(slots=True)
class MovimientoMedicamento:
    id: Optional[int] = None
    medicamento_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    tipo: TipoMovimientoStock = TipoMovimientoStock.ENTRADA
    cantidad: int = 0
    motivo: Optional[str] = None
    receta_id: Optional[int] = None
    dispensacion_id: Optional[int] = None
    personal_id: Optional[int] = None

    def validar(self) -> None:
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        _ensure_non_negative(self.cantidad, "cantidad")
        self.motivo = _strip_or_none(self.motivo)

    def delta_stock(self) -> int:
        if self.tipo == TipoMovimientoStock.ENTRADA:
            return self.cantidad
        if self.tipo == TipoMovimientoStock.SALIDA:
            return -self.cantidad
        return self.cantidad

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        d["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return d


@dataclass(slots=True)
class MovimientoMaterial:
    id: Optional[int] = None
    material_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    tipo: TipoMovimientoStock = TipoMovimientoStock.ENTRADA
    cantidad: int = 0
    motivo: Optional[str] = None
    personal_id: Optional[int] = None

    def validar(self) -> None:
        _ensure_positive_id(self.material_id, "material_id")
        _ensure_non_negative(self.cantidad, "cantidad")
        self.motivo = _strip_or_none(self.motivo)

    def delta_stock(self) -> int:
        if self.tipo == TipoMovimientoStock.ENTRADA:
            return self.cantidad
        if self.tipo == TipoMovimientoStock.SALIDA:
            return -self.cantidad
        return self.cantidad

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        d["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return d


@dataclass(slots=True)
class Cita:
    id: Optional[int] = None
    paciente_id: int = 0
    medico_id: int = 0
    sala_id: int = 0
    inicio: datetime = field(default_factory=datetime.now)
    fin: datetime = field(default_factory=datetime.now)
    estado: EstadoCita = EstadoCita.PROGRAMADA
    motivo: Optional[str] = None
    notas: Optional[str] = None
    override_ok: bool = False
    override_nota: Optional[str] = None
    override_personal_id: Optional[int] = None
    override_fecha_hora: Optional[datetime] = None

    def validar(self) -> None:
        _ensure_positive_id(self.paciente_id, "paciente_id")
        _ensure_positive_id(self.medico_id, "medico_id")
        _ensure_positive_id(self.sala_id, "sala_id")

        if self.fin <= self.inicio:
            raise ValidationError("fin debe ser posterior a inicio.")

        self.motivo = _strip_or_none(self.motivo)
        self.notas = _strip_or_none(self.notas)
        self.override_nota = _strip_or_none(self.override_nota)

        if self.override_ok:
            self.override_nota = _require_override_note(self.override_nota)
            if self.override_personal_id is None:
                raise ValidationError("override_personal_id obligatorio para guardar con incidencia.")
            _ensure_positive_id(self.override_personal_id, "override_personal_id")
            if self.override_fecha_hora is None:
                raise ValidationError("override_fecha_hora obligatorio para guardar con incidencia.")

    def duracion_minutos(self) -> int:
        return int((self.fin - self.inicio).total_seconds() // 60)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["inicio"] = self.inicio.isoformat(sep=" ", timespec="seconds")
        d["fin"] = self.fin.isoformat(sep=" ", timespec="seconds")
        d["estado"] = self.estado.value
        if self.override_fecha_hora is not None:
            d["override_fecha_hora"] = self.override_fecha_hora.isoformat(sep=" ", timespec="seconds")
        return d


@dataclass(slots=True)
class Receta:
    id: Optional[int] = None
    paciente_id: int = 0
    medico_id: int = 0
    fecha: datetime = field(default_factory=datetime.now)
    observaciones: Optional[str] = None

    def validar(self) -> None:
        _ensure_positive_id(self.paciente_id, "paciente_id")
        _ensure_positive_id(self.medico_id, "medico_id")
        self.observaciones = _strip_or_none(self.observaciones)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["fecha"] = self.fecha.isoformat(sep=" ", timespec="seconds")
        return d


@dataclass(slots=True)
class RecetaLinea:
    id: Optional[int] = None
    receta_id: int = 0
    medicamento_id: int = 0
    dosis: str = ""
    duracion_dias: Optional[int] = None
    instrucciones: Optional[str] = None

    def validar(self) -> None:
        _ensure_positive_id(self.receta_id, "receta_id")
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        self.dosis = _require_non_empty(self.dosis, "dosis")
        if self.duracion_dias is not None and self.duracion_dias <= 0:
            raise ValidationError("duracion_dias debe ser > 0 si se indica.")
        self.instrucciones = _strip_or_none(self.instrucciones)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Dispensacion:
    id: Optional[int] = None
    receta_id: int = 0
    receta_linea_id: Optional[int] = None
    medicamento_id: int = 0
    personal_id: int = 0
    fecha_hora: datetime = field(default_factory=datetime.now)
    cantidad: int = 0
    observaciones: Optional[str] = None
    override_ok: bool = False
    override_nota: Optional[str] = None
    override_personal_id: Optional[int] = None
    override_fecha_hora: Optional[datetime] = None

    def validar(self) -> None:
        _ensure_positive_id(self.receta_id, "receta_id")
        _ensure_positive_id(self.medicamento_id, "medicamento_id")
        _ensure_positive_id(self.personal_id, "personal_id")
        _ensure_non_negative(self.cantidad, "cantidad")

        self.observaciones = _strip_or_none(self.observaciones)
        self.override_nota = _strip_or_none(self.override_nota)

        if self.override_ok:
            self.override_nota = _require_override_note(self.override_nota)
            if self.override_personal_id is None:
                raise ValidationError("override_personal_id obligatorio para guardar con incidencia.")
            _ensure_positive_id(self.override_personal_id, "override_personal_id")
            if self.override_fecha_hora is None:
                raise ValidationError("override_fecha_hora obligatorio para guardar con incidencia.")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        if self.override_fecha_hora is not None:
            d["override_fecha_hora"] = self.override_fecha_hora.isoformat(sep=" ", timespec="seconds")
        return d


@dataclass(slots=True)
class Incidencia:
    id: Optional[int] = None
    tipo: TipoIncidencia = TipoIncidencia.CITA_SIN_CUADRANTE
    severidad: SeveridadIncidencia = SeveridadIncidencia.WARNING
    estado: EstadoIncidencia = EstadoIncidencia.ABIERTA
    fecha_hora: datetime = field(default_factory=datetime.now)
    descripcion: str = ""
    medico_id: Optional[int] = None
    personal_id: Optional[int] = None
    cita_id: Optional[int] = None
    dispensacion_id: Optional[int] = None
    receta_id: Optional[int] = None
    confirmado_por_personal_id: int = 0
    nota_override: str = ""

    def validar(self) -> None:
        self.descripcion = _require_non_empty(self.descripcion, "descripcion")
        self.nota_override = _require_non_empty(self.nota_override, "nota_override")
        _ensure_positive_id(self.confirmado_por_personal_id, "confirmado_por_personal_id")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value
        d["severidad"] = self.severidad.value
        d["estado"] = self.estado.value
        d["fecha_hora"] = self.fecha_hora.isoformat(sep=" ", timespec="seconds")
        return d
