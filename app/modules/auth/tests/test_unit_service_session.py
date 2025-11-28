import pytest

from app import db
from app.modules.auth.models import User, UserSession
from app.modules.auth.services import AuthenticationService

# --- FIXTURES ---


@pytest.fixture
def auth_service():
    return AuthenticationService()


@pytest.fixture(autouse=True)
def setup_database(test_app):
    with test_app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture
def user_with_session_ids(test_app):  # <--- CAMBIO DE NOMBRE PARA SER CLARO
    """
    Crea datos y devuelve SOLO LOS IDs.
    Esto evita el error DetachedInstanceError.
    """
    with test_app.app_context():
        user = User(email="owner@example.com", password="password123")
        db.session.add(user)
        db.session.commit()

        # IMPORTANTE: Guardamos los IDs en variables simples antes de salir
        user_id = user.id

        session_model = UserSession(
            user_id=user_id, token="fake_token_123", ip_address="127.0.0.1", device="Chrome Test"
        )
        db.session.add(session_model)
        db.session.commit()

        session_id = session_model.id

        # Devolvemos tuplas de IDs
        return user_id, session_id


# --- TESTS CORREGIDOS ---


def test_revoke_session_success(test_app, auth_service, user_with_session_ids):
    # 1. Recibimos solo los números (IDs)
    user_id, session_id = user_with_session_ids

    with test_app.app_context():
        # 2. Volvemos a buscar los objetos DENTRO de la sesión activa de este test
        user = User.query.get(user_id)

        # Ejecutar la revocación
        result = auth_service.revoke_session(user, session_id)

        # Verificar
        assert result is True
        assert UserSession.query.get(session_id) is None


def test_revoke_session_foreign_user(test_app, auth_service, user_with_session_ids):
    # 1. Recibimos IDs
    _, session_id = user_with_session_ids  # No necesitamos el usuario owner aquí

    with test_app.app_context():
        # Creamos al atacante
        attacker = User(email="attacker@example.com", password="password123")
        db.session.add(attacker)
        db.session.commit()

        # El atacante intenta borrar la sesión usando el ID que nos pasó la fixture
        result = auth_service.revoke_session(attacker, session_id)

        # Verificar
        assert result is False
        assert UserSession.query.get(session_id) is not None


def test_revoke_non_existent_session(test_app, auth_service, user_with_session_ids):
    user_id, _ = user_with_session_ids

    with test_app.app_context():
        user = User.query.get(user_id)
        result = auth_service.revoke_session(user, 9999)

        assert result is False
