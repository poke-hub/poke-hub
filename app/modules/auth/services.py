import base64
import io
import json
import os
import secrets
import string

import pyotp
import qrcode
from cryptography.fernet import Fernet
from flask import current_app, request, session
from flask_login import current_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.modules.auth.models import User, UserSession
from app.modules.auth.repositories import UserRepository
from app.modules.profile.models import UserProfile
from app.modules.profile.repositories import UserProfileRepository
from app.modules.shopping_cart.repositories import ShoppingCartRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService


def get_fernet():
    key = current_app.config["ENCRYPTION_KEY"]
    return Fernet(key.encode())


def encrypt_data(data):
    if data is None:
        return None
    fernet = get_fernet()
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data):
    if encrypted_data is None:
        return None
    fernet = get_fernet()
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return None


class AuthenticationService(BaseService):
    def __init__(self):
        super().__init__(UserRepository())
        self.user_profile_repository = UserProfileRepository()
        self.shopping_cart_repository = ShoppingCartRepository()

    def login(self, email, password, remember=True):
        """
        Devuelve:
         - True: Login exitoso y sesión creada (2FA desactivado).
         - False: Credenciales incorrectas.
         - Objeto User: Credenciales correctas, pero requiere 2FA.
        """
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            if user.is_two_factor_enabled:
                return user
            else:
                login_user(user, remember=remember)
                self.create_user_session(user)  # <-- CREAMOS LA SESIÓN EN BBDD
                return True

        return False

    def create_user_session(self, user):
        """Registra la sesión actual en la base de datos."""
        token = secrets.token_urlsafe(32)

        # Obtener información del dispositivo
        user_agent = request.user_agent
        platform = user_agent.platform or "Unknown OS"
        browser = user_agent.browser or "Unknown Browser"
        version = user_agent.version or ""
        device_name = f"{platform} - {browser} {version}".strip()
        ip = request.remote_addr

        new_session = UserSession(user_id=user.id, token=token, ip_address=ip, device=device_name)

        db.session.add(new_session)
        db.session.commit()

        # Guardar el token en la cookie del navegador
        session["app_session_token"] = token

    def get_active_sessions(self, user):
        """Obtiene todas las sesiones activas del usuario."""
        return user.sessions.order_by(UserSession.last_seen.desc()).all()

    def revoke_session(self, user, session_id):
        """Elimina una sesión específica."""
        user_session = UserSession.query.filter_by(id=session_id, user_id=user.id).first()
        if user_session:
            db.session.delete(user_session)
            db.session.commit()
            return True
        return False

    def logout_session(self):
        """Elimina la sesión actual de la base de datos usando el token de la cookie."""
        token = session.get("app_session_token")
        if token:
            # Buscar la sesión en BBDD por el token actual
            user_session = UserSession.query.filter_by(token=token).first()
            if user_session:
                db.session.delete(user_session)
                db.session.commit()

            # Limpiar la referencia de la sesión
            session.pop("app_session_token", None)

    def is_email_available(self, email: str) -> bool:
        return self.repository.get_by_email(email) is None

    def create_with_profile(self, **kwargs):
        try:
            email = kwargs.pop("email", None)
            password = kwargs.pop("password", None)
            name = kwargs.pop("name", None)
            surname = kwargs.pop("surname", None)

            if not email:
                raise ValueError("Email is required.")
            if not password:
                raise ValueError("Password is required.")
            if not name:
                raise ValueError("Name is required.")
            if not surname:
                raise ValueError("Surname is required.")

            user_data = {"email": email, "password": password}

            profile_data = {
                "name": name,
                "surname": surname,
            }

            user = self.create(commit=False, **user_data)
            profile_data["user_id"] = user.id
            self.user_profile_repository.create(**profile_data)
            shopping_cart_data = {"user_id": user.id}
            self.shopping_cart_repository.create(**shopping_cart_data)
            self.repository.session.commit()
        except Exception as exc:
            self.repository.session.rollback()
            raise exc
        return user

    def update_profile(self, user_profile_id, form):
        if form.validate():
            updated_instance = self.update(user_profile_id, **form.data)
            return updated_instance, None

        return None, form.errors

    def get_authenticated_user(self) -> User | None:
        if current_user.is_authenticated:
            return current_user
        return None

    def get_authenticated_user_profile(self) -> UserProfile | None:
        if current_user.is_authenticated:
            return current_user.profile
        return None

    def temp_folder_by_user(self, user: User) -> str:
        return os.path.join(uploads_folder_name(), "temp", str(user.id))

    def generate_2fa_secret(self):
        return pyotp.random_base32()

    def get_2fa_provisioning_uri(self, user_email, secret):
        return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="Poké-Hub")

    def generate_qr_code_base64(self, uri):
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def verify_2fa_token(self, user: User, token: str) -> bool:
        secret = decrypt_data(user.two_factor_secret)
        if secret is None:
            return False
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def generate_recovery_codes(self):
        alphabet = string.ascii_uppercase + string.digits
        codes = []
        for _ in range(10):
            codes.append("".join(secrets.choice(alphabet) for _ in range(10)))
        hashed_codes = [generate_password_hash(code) for code in codes]
        return codes, json.dumps(hashed_codes)

    def verify_recovery_code(self, user: User, provided_code: str) -> bool:
        if not user.two_factor_recovery_codes:
            return False

        hashed_codes = json.loads(user.two_factor_recovery_codes)
        new_hashed_codes = []
        code_was_valid = False

        for hashed_code in hashed_codes:
            if not code_was_valid and check_password_hash(hashed_code, provided_code):
                code_was_valid = True
            else:
                new_hashed_codes.append(hashed_code)

        if code_was_valid:
            user.two_factor_recovery_codes = json.dumps(new_hashed_codes)
            db.session.commit()

        return code_was_valid

    def set_user_2fa_secret(self, user: User, secret: str):
        user.two_factor_secret = encrypt_data(secret)
        db.session.commit()

    def set_user_2fa_recovery_codes(self, user: User, hashed_codes_json: str):
        user.two_factor_recovery_codes = hashed_codes_json
        db.session.commit()

    def set_user_2fa_enabled(self, user: User, is_enabled: bool):
        user.is_two_factor_enabled = is_enabled
        db.session.commit()

    def clear_user_2fa_data(self, user: User):
        user.is_two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_recovery_codes = None
        db.session.commit()

    def check_user_password(self, user: User, password: str) -> bool:
        return user.check_password(password)
