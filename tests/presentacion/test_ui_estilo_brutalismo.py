# ruff: noqa: E402
"""Smoke tests de estilo brutalista para páginas UI."""

import pytest


django = pytest.importorskip("django")
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def cliente():
    return Client()


@pytest.fixture
def usuario(db):
    modelo = get_user_model()
    return modelo.objects.create_user(
        username="usuario_brutal",
        email="brutal@example.com",
        password="password_pruebas",
    )


def test_login_contiene_panel_y_boton_entrar(cliente):
    respuesta = cliente.get("/ui/login")
    html = respuesta.content.decode("utf-8")

    assert respuesta.status_code == 200
    assert "panel" in html
    assert "Entrar" in html
    assert "toggle" in html.lower() and "tema" in html.lower()


def test_registro_contiene_titulo_y_selector_tipo_cuenta(cliente):
    respuesta = cliente.get("/ui/registro")
    html = respuesta.content.decode("utf-8")

    assert respuesta.status_code == 200
    assert "Crear cuenta" in html
    assert 'name="tipo_cuenta"' in html
    assert "toggle" in html.lower() and "tema" in html.lower()


def test_muro_autenticado_contiene_bloque_crear_publicacion(cliente, usuario):
    assert cliente.login(username="usuario_brutal", password="password_pruebas")

    respuesta = cliente.get("/ui/muro")
    html = respuesta.content.decode("utf-8")

    assert respuesta.status_code == 200
    assert "Crear publicación" in html
    assert "toggle" in html.lower() and "tema" in html.lower()
