import pyotp

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService


# --- Helpers (Mantener igual) ---
def login(test_client, email, password):
    return test_client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def logout(test_client):
    return test_client.get("/logout", follow_redirects=True)


def clean_user_state(test_client):
    try:
        test_client.cookie_jar.clear()
        logout(test_client)
    except Exception:
        pass

    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        if user:
            user.is_two_factor_enabled = False
            user.two_factor_secret = None
            user.two_factor_recovery_codes = None
            db.session.commit()
        db.session.remove()


def test_full_2fa_activation_flow(test_client):
    """
    Test de integración para el flujo completo de activación de 2FA.
    """
    clean_user_state(test_client)

    login(test_client, "test@example.com", "test1234")

    response = test_client.post("/profile/2fa/setup")
    assert response.status_code == 200
    data = response.get_json()
    assert "secret" in data
    secret = data["secret"]

    with test_client.application.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        auth_service = AuthenticationService()
        auth_service.set_user_2fa_secret(user, secret)
        db.session.commit()

    totp = pyotp.TOTP(secret)
    valid_token = totp.now()

    response = test_client.post("/profile/2fa/enable", data={"token": valid_token}, follow_redirects=True)

    assert response.status_code == 200
    assert b"Copy all codes" in response.data

    logout(test_client)


def test_login_with_2fa_enabled(test_client):
    """
    Verificar que el login redirige a /verify-2fa si 2FA está activado.
    """
    clean_user_state(test_client)

    secret = "5JEIF3ANYS7UJKZEN7PZJFG5RHTNRPR2"

    with test_client.application.app_context():
        auth_service = AuthenticationService()
        user = User.query.filter_by(email="test@example.com").first()

        auth_service.set_user_2fa_secret(user, secret)
        _, hashed_codes = auth_service.generate_recovery_codes()
        auth_service.set_user_2fa_recovery_codes(user, hashed_codes)
        auth_service.set_user_2fa_enabled(user, True)

        db.session.commit()
        db.session.expire_all()

    # Intento de Login
    response = test_client.post(
        "/login", data={"email": "test@example.com", "password": "test1234"}, follow_redirects=False
    )

    # Verificación: Debe redirigir a la página de verificación, NO al home (/)
    assert response.status_code == 302
    assert response.location == "/login/verify-2fa"

    # Verificación de fallo con token incorrecto
    response = test_client.post("/login/verify-2fa", data={"token": "000000"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid code. Please try again." in response.data

    # Limpieza final
    logout(test_client)
