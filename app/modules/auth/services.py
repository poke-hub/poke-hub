import base64
import io
import json
import os
import secrets
import string

import pyotp
import qrcode
from cryptography.fernet import Fernet
from flask import current_app
from flask_login import current_user, login_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.modules.auth.models import User
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
        Modificado para manejar el flujo 2FA.
        Devuelve:
         - True: Login exitoso (2FA desactivado).
         - False: Credenciales incorrectas.
         - Objeto User: Credenciales correctas, pero 2FA está activado.
        """
        user = self.repository.get_by_email(email)
        if user is not None and user.check_password(password):
            if user.is_two_factor_enabled:
                return user
            else:
                login_user(user, remember=remember)
                return True

        return False

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
        """Genera un nuevo secreto 2FA."""
        return pyotp.random_base32()

    def get_2fa_provisioning_uri(self, user_email, secret):
        """Genera la URI para el código QR."""
        return pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="Poké-Hub")

    def generate_qr_code_base64(self, uri):
        """Genera un código QR a partir de la URI y lo devuelve como imagen base64."""
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    def verify_2fa_token(self, user: User, token: str) -> bool:
        """Verifica un token TOTP de 6 dígitos."""
        secret = decrypt_data(user.two_factor_secret)
        if secret is None:
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def generate_recovery_codes(self):
        """Genera una lista de 10 códigos de recuperación."""

        alphabet = string.ascii_uppercase + string.digits

        codes = []
        for _ in range(10):
            codes.append("".join(secrets.choice(alphabet) for _ in range(10)))

        hashed_codes = [generate_password_hash(code) for code in codes]

        return codes, json.dumps(hashed_codes)

    def verify_recovery_code(self, user: User, provided_code: str) -> bool:
        """Verifica un código de recuperación y lo invalida."""
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
        """Guarda el secreto del usuario."""
        user.two_factor_secret = encrypt_data(secret)
        db.session.commit()

    def set_user_2fa_recovery_codes(self, user: User, hashed_codes_json: str):
        """Guarda los códigos de recuperación del usuario."""
        user.two_factor_recovery_codes = hashed_codes_json
        db.session.commit()

    def set_user_2fa_enabled(self, user: User, is_enabled: bool):
        """Activa o desactiva el 2FA para el usuario."""
        user.is_two_factor_enabled = is_enabled
        db.session.commit()

    def clear_user_2fa_data(self, user: User):
        """Limpia todos los datos relacionados con 2FA del usuario."""
        user.is_two_factor_enabled = False
        user.two_factor_secret = None
        user.two_factor_recovery_codes = None
        db.session.commit()

    def check_user_password(self, user: User, password: str) -> bool:
        """Función de ayuda para verificar la contraseña."""
        return user.check_password(password)
