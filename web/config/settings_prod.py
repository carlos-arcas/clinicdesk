"""Settings de producción orientados a entorno Docker."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DEBUG = False
SECRET_KEY = os.getenv("APP_SECRET_KEY", "")

ALLOWED_HOSTS = [host.strip() for host in os.getenv("APP_ALLOWED_HOSTS", "").split(",") if host.strip()]

DB_NAME = os.getenv("DB_NAME", "clinicdesk")
DB_USER = os.getenv("DB_USER", "clinicdesk")
DB_PASSWORD = os.getenv("DB_PASSWORD", "clinicdesk")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "0") == "1"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "0") == "1"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
