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
