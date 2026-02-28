# domain/exceptions.py
"""
Excepciones del dominio.

Propósito:
- Distinguir errores de reglas de negocio (dominio) de errores técnicos (DB/UI/red).
- Permitir que la capa de aplicación/UI traduzca errores a mensajes para el usuario.
"""


class DomainError(Exception):
    """Error base del dominio."""


class ValidationError(DomainError):
    """Entidad en estado inválido o violación de invariantes."""


class BusinessRuleError(DomainError):
    """Violación de regla de negocio (p. ej., solape de cita detectado en un caso de uso)."""


class AuthorizationError(DomainError):
    """Operación denegada por falta de permisos del usuario actual."""
