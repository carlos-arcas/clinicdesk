from __future__ import annotations

from typing import Callable


_TRANSLATIONS = {
    "es": {
        "app.title": "ClinicDesk",
        "menu.file": "Archivo",
        "menu.csv": "Importar/Exportar CSV…",
        "menu.logout": "Cerrar sesión",
        "menu.exit": "Salir",
        "menu.language": "Idioma",
        "lang.es": "Español",
        "lang.en": "English",
        "login.title": "Acceso seguro",
        "login.user": "Usuario",
        "login.password": "Contraseña",
        "login.submit": "Iniciar sesión",
        "login.demo": "Entrar en modo demo",
        "login.first_run": "Primera ejecución: crea credenciales de administrador.",
        "login.confirm_password": "Confirmar contraseña",
        "login.create": "Crear credenciales",
        "login.error.required": "Usuario y contraseña son obligatorios.",
        "login.error.mismatch": "Las contraseñas no coinciden.",
        "login.error.invalid": "Credenciales inválidas.",
        "login.error.locked": "Acceso bloqueado temporalmente por intentos fallidos.",
        "login.error.demo_disabled": "Modo demo no permitido para esta base de datos.",
        "login.ok.created": "Credenciales creadas correctamente.",
        "pacientes.id": "ID",
        "pacientes.tipo_documento": "Tipo de documento",
        "pacientes.documento": "Documento",
        "pacientes.nombre": "Nombre",
        "pacientes.apellidos": "Apellidos",
        "pacientes.nombre_completo": "Nombre completo",
        "pacientes.telefono": "Teléfono",
        "pacientes.email": "Correo electrónico",
        "pacientes.fecha_nacimiento": "Fecha de nacimiento",
        "pacientes.direccion": "Dirección",
        "pacientes.activo": "Activo",
        "pacientes.num_historia": "N.º historia",
        "pacientes.alergias": "Alergias",
        "pacientes.observaciones": "Observaciones",
        "comun.si": "Sí",
        "comun.no": "No",
        "pacientes.tooltip.listado": "Documento: {documento}\nTeléfono: {telefono}\nActivo: {estado}",
        "pacientes.historial.boton": "Historial",
        "pacientes.historial.titulo": "Historial del paciente",
        "pacientes.historial.cargando": "Cargando historial…",
        "pacientes.historial.error": "Error al cargar el historial del paciente.",
        "pacientes.historial.header": "{nombre} · {documento} · {telefono} · {email}",
        "pacientes.historial.tab.resumen": "Resumen",
        "pacientes.historial.tab.citas": "Citas",
        "pacientes.historial.tab.recetas": "Medicaciones/Recetas",
        "pacientes.historial.tab.incidencias": "Incidencias",
        "pacientes.historial.resumen.descripcion": "Detalle clínico del paciente seleccionado.",
        "pacientes.historial.citas.fecha": "Fecha",
        "pacientes.historial.citas.hora_inicio": "Hora inicio",
        "pacientes.historial.citas.hora_fin": "Hora fin",
        "pacientes.historial.citas.medico": "Médico",
        "pacientes.historial.citas.estado": "Estado",
        "pacientes.historial.citas.resumen": "Resumen/Nota",
        "pacientes.historial.citas.longitud": "longitud",
        "pacientes.historial.citas.incidencias": "Incidencias",
        "pacientes.historial.sin_citas": "Sin citas registradas",
        "pacientes.historial.recetas.id": "ID",
        "pacientes.historial.recetas.fecha": "Fecha",
        "pacientes.historial.recetas.medico": "Médico",
        "pacientes.historial.recetas.estado": "Estado",
        "pacientes.historial.recetas.sin_datos": "Pendiente",
        "pacientes.historial.pendiente": "Pendiente",
    },
    "en": {
        "app.title": "ClinicDesk",
        "menu.file": "File",
        "menu.csv": "Import/Export CSV…",
        "menu.logout": "Log out",
        "menu.exit": "Exit",
        "menu.language": "Language",
        "lang.es": "Spanish",
        "lang.en": "English",
        "login.title": "Secure access",
        "login.user": "User",
        "login.password": "Password",
        "login.submit": "Sign in",
        "login.demo": "Enter demo mode",
        "login.first_run": "First run: create administrator credentials.",
        "login.confirm_password": "Confirm password",
        "login.create": "Create credentials",
        "login.error.required": "User and password are required.",
        "login.error.mismatch": "Passwords do not match.",
        "login.error.invalid": "Invalid credentials.",
        "login.error.locked": "Access temporarily blocked due to failed attempts.",
        "login.error.demo_disabled": "Demo mode is not allowed for this database.",
        "login.ok.created": "Credentials successfully created.",
        "pacientes.id": "ID",
        "pacientes.tipo_documento": "Document type",
        "pacientes.documento": "Document",
        "pacientes.nombre": "Name",
        "pacientes.apellidos": "Last name",
        "pacientes.nombre_completo": "Full name",
        "pacientes.telefono": "Phone",
        "pacientes.email": "Email",
        "pacientes.fecha_nacimiento": "Birth date",
        "pacientes.direccion": "Address",
        "pacientes.activo": "Active",
        "pacientes.num_historia": "Clinical record no.",
        "pacientes.alergias": "Allergies",
        "pacientes.observaciones": "Notes",
        "comun.si": "Yes",
        "comun.no": "No",
        "pacientes.tooltip.listado": "Document: {documento}\nPhone: {telefono}\nActive: {estado}",
        "pacientes.historial.boton": "History",
        "pacientes.historial.titulo": "Patient history",
        "pacientes.historial.cargando": "Loading history…",
        "pacientes.historial.error": "Error loading patient history.",
        "pacientes.historial.header": "{nombre} · {documento} · {telefono} · {email}",
        "pacientes.historial.tab.resumen": "Summary",
        "pacientes.historial.tab.citas": "Appointments",
        "pacientes.historial.tab.recetas": "Medications/Prescriptions",
        "pacientes.historial.tab.incidencias": "Incidents",
        "pacientes.historial.resumen.descripcion": "Clinical detail of the selected patient.",
        "pacientes.historial.citas.fecha": "Date",
        "pacientes.historial.citas.hora_inicio": "Start time",
        "pacientes.historial.citas.hora_fin": "End time",
        "pacientes.historial.citas.medico": "Doctor",
        "pacientes.historial.citas.estado": "Status",
        "pacientes.historial.citas.resumen": "Summary/Note",
        "pacientes.historial.citas.longitud": "length",
        "pacientes.historial.citas.incidencias": "Incidents",
        "pacientes.historial.sin_citas": "No appointments registered",
        "pacientes.historial.recetas.id": "ID",
        "pacientes.historial.recetas.fecha": "Date",
        "pacientes.historial.recetas.medico": "Doctor",
        "pacientes.historial.recetas.estado": "Status",
        "pacientes.historial.recetas.sin_datos": "Pending",
        "pacientes.historial.pendiente": "Pending",
    },
}


class I18nManager:
    def __init__(self, language: str = "es") -> None:
        self._language = language if language in _TRANSLATIONS else "es"
        self._listeners: list[Callable[[], None]] = []

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in _TRANSLATIONS or language == self._language:
            return
        self._language = language
        for listener in list(self._listeners):
            listener()

    def t(self, key: str) -> str:
        return _TRANSLATIONS.get(self._language, {}).get(key, key)

    def subscribe(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)
