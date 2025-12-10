from unittest.mock import MagicMock, patch

import pytest
from flask import url_for

from app import db
from app.modules.auth.models import User, UserSession
from app.modules.conftest import login, logout
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DataSet


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        if not user:
            user_test = User(email="user@example.com", password="test1234")
            db.session.add(user_test)
            db.session.commit()

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
    with patch("app.modules.profile.routes.TwoFactorEnableForm") as mock_enable:
        enable_instance = mock_enable.return_value
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
    login(test_client, "user@example.com", "test1234")

    service_instance = mock_auth_service.return_value
    service_instance.get_active_sessions.return_value = []

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
    login(test_client, "user@example.com", "test1234")

    mock_session = MagicMock(spec=UserSession)
    mock_session.device = "Chrome on Windows"
    mock_session.ip_address = "192.168.1.50"
    mock_session.token = "dummy_token"

    mock_session.last_seen.strftime.return_value = "10:00 AM"
    mock_session.created_at.strftime.return_value = "2024-01-01"

    service_instance = mock_auth_service.return_value
    service_instance.get_active_sessions.return_value = [mock_session]

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
    login(test_client, "user@example.com", "test1234")

    service_instance = mock_auth_service.return_value
    service_instance.revoke_session.return_value = True

    session_id = 99

    response = test_client.post(url_for("profile.revoke_session", session_id=session_id), follow_redirects=True)

    assert response.status_code == 200
    assert b"Session revoked successfully" in response.data

    service_instance.revoke_session.assert_called_once()
    call_args = service_instance.revoke_session.call_args
    assert call_args[0][1] == session_id

    logout(test_client)


def test_view_profile_unit(test_client):
    """
    Test unitario para la vista de perfil (view_profile).
    Mockea la base de datos para no depender de ella.
    """
    user_id = 1

    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.profile = MagicMock()

    ds1 = MagicMock()
    ds1.ds_meta_data.dataset_doi = "10.1234/ds1"
    ds1.ds_meta_data.title = "Dataset 1"
    ds1.ds_meta_data.description = "Description 1"
    ds1.ds_meta_data.publication_type.name = "NONE"
    ds1.created_at.strftime.return_value = "2024-01-01"
    ds1.get_file_total_size_for_human.return_value = "1.0 MB"
    ds1.get_pokehub_doi.return_value = "http://localhost/doi/10.1234/ds1"

    ds2 = MagicMock()
    ds2.ds_meta_data.dataset_doi = None
    ds2.ds_meta_data.title = "Dataset 2"
    ds2.ds_meta_data.description = "Description 2"
    ds2.ds_meta_data.publication_type.name = "NONE"
    ds2.created_at.strftime.return_value = "2024-01-02"
    ds2.get_file_total_size_for_human.return_value = "2.0 MB"
    ds2.get_pokehub_doi.return_value = "http://localhost/doi/10.1234/ds2"

    mock_dataset_pagination = MagicMock()
    mock_dataset_pagination.items = [ds1, ds2]
    mock_dataset_pagination.pages = 1
    mock_dataset_pagination.page = 1
    mock_dataset_pagination.has_prev = False
    mock_dataset_pagination.has_next = False
    mock_dataset_pagination.iter_pages.return_value = [1]

    with patch("app.modules.profile.routes.db") as mock_db:
        def query_side_effect(model):
            query_mock = MagicMock()
            if model == User:
                query_mock.get.return_value = mock_user
            elif model == DataSet:
             
                filter_mock = query_mock.filter.return_value
                order_by_mock = filter_mock.order_by.return_value
                order_by_mock.paginate.return_value = mock_dataset_pagination

                filter_mock.count.return_value = 10
            return query_mock

        mock_db.session.query.side_effect = query_side_effect

        response = test_client.get(f"/profile/{user_id}")

        assert response.status_code == 200


def test_view_profile_404_unit(test_client):
    """
    Test unitario para verificar que devuelve 404 si el usuario no existe.
    """
    with patch("app.modules.profile.routes.db") as mock_db:
        mock_db.session.query.return_value.get.return_value = None

        response = test_client.get("/profile/999")
        assert response.status_code == 404

