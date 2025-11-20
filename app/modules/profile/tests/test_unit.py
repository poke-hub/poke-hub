from unittest.mock import MagicMock, patch

import pytest
from flask import url_for

from app import db
from app.modules.auth.models import User, UserSession
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        # Verificar si el usuario ya existe para evitar errores de unicidad al re-ejecutar
        user = User.query.filter_by(email="user@example.com").first()
        if not user:
            user_test = User(email="user@example.com", password="test1234")
            db.session.add(user_test)
            db.session.commit()

            # Crear perfil asociado
            profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
            db.session.add(profile)
            db.session.commit()

    yield test_client


@pytest.fixture
def mock_auth_service():
    """
    Mock del AuthenticationService para interceptar llamadas en las rutas de profile.
    """
    with patch("app.modules.profile.routes.AuthenticationService") as mock:
        yield mock


@pytest.fixture
def mock_forms():
    """
    SOLUCIÓN DEL ERROR:
    Mockea los formularios de 2FA para evitar el error de 'csrf_token' en Jinja2.
    Simulamos que el formulario tiene el atributo csrf_token.current_token.
    """
    # Es importante parchear donde se IMPORTA la clase (en routes), no donde se define.
    with patch("app.modules.profile.routes.TwoFactorEnableForm") as mock_enable:
        # Configuramos la instancia que devuelve el formulario
        enable_instance = mock_enable.return_value
        # Le damos el atributo que busca el HTML
        enable_instance.csrf_token.current_token = "dummy_token"

        yield mock_enable


def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert response.status_code == 200, "The profile editing page could not be accessed."
    assert b"Edit profile" in response.data, "The expected content is not present on the page"

    logout(test_client)


def test_security_settings_page_loads(test_client, mock_auth_service, mock_forms):
    """
    Verifica que la página de seguridad carga correctamente (200 OK).
    Se añade 'mock_forms' para evitar el error de renderizado de Jinja2.
    """
    # 1. Login
    login(test_client, "user@example.com", "test1234")

    # 2. Configurar Mock del servicio
    service_instance = mock_auth_service.return_value
    service_instance.get_active_sessions.return_value = []

    # 3. Ejecutar request
    response = test_client.get(url_for("profile.security_settings"))

    assert response.status_code == 200
    assert b"Security Settings" in response.data
    service_instance.get_active_sessions.assert_called_once()

    logout(test_client)


def test_security_settings_displays_sessions(test_client, mock_auth_service, mock_forms):
    """
    Verifica que si el servicio devuelve sesiones, estas se pintan en el HTML.
    Se añade 'mock_forms' para evitar el error de renderizado de Jinja2.
    """
    # 1. Login
    login(test_client, "user@example.com", "test1234")

    # 2. Configurar Mock con datos simulados
    mock_session = MagicMock(spec=UserSession)
    mock_session.device = "Chrome on Windows"
    mock_session.ip_address = "192.168.1.50"
    mock_session.token = "dummy_token"
    # Configuramos el return value de strftime para que no falle al renderizar el template
    mock_session.last_seen.strftime.return_value = "10:00 AM"
    mock_session.created_at.strftime.return_value = "2024-01-01"

    service_instance = mock_auth_service.return_value
    service_instance.get_active_sessions.return_value = [mock_session]

    # 3. Ejecutar request
    response = test_client.get(url_for("profile.security_settings"))

    assert response.status_code == 200
    assert b"Chrome on Windows" in response.data
    assert b"192.168.1.50" in response.data

    logout(test_client)


def test_revoke_session_action(test_client, mock_auth_service, mock_forms):
    """
    Verifica que la ruta de revocar sesión llama al método correcto del servicio.
    Se añade 'mock_forms' porque al redirigir (follow_redirects=True) se renderiza de nuevo la página.
    """
    # 1. Login
    login(test_client, "user@example.com", "test1234")

    # 2. Configurar Mock para simular éxito
    service_instance = mock_auth_service.return_value
    service_instance.revoke_session.return_value = True

    # ID ficticio
    session_id = 99

    # 3. Ejecutar POST request para revocar
    # Al tener follow_redirects=True, tras el POST hace un GET a security_settings,
    # por lo que necesitamos mock_forms también aquí.
    response = test_client.post(url_for("profile.revoke_session", session_id=session_id), follow_redirects=True)

    assert response.status_code == 200
    assert b"Session revoked successfully" in response.data

    # 4. Verificamos llamada al servicio
    service_instance.revoke_session.assert_called_once()
    call_args = service_instance.revoke_session.call_args
    assert call_args[0][1] == session_id

    logout(test_client)
