"""Settings de desarrollo para entornos locales."""

from __future__ import annotations

from .settings_prod import *  # noqa: F403

DEBUG = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
