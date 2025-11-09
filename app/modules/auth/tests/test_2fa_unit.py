import pytest
import pyotp
import json
from unittest.mock import patch, MagicMock, patch
from cryptography.fernet import Fernet

from app.modules.auth.services import AuthenticationService

from app.modules.auth.services import encrypt_data, decrypt_data

# Clave de encriptación de prueba
TEST_ENCRYPTION_KEY = Fernet.generate_key().decode()

@pytest.fixture
def auth_service():
    """
    Fixture que crea una instancia del AuthenticationService
    para cada prueba.
    """
    return AuthenticationService()

def test_encrypt_decrypt_roundtrip():
    """
    Verifica que un secreto encriptado puede ser desencriptado
    correctamente y devuelve el valor original.
    """
    original_secret = "5JEIF3ANYS7UJKZEN7PZJFG5RHTNRPR2"
    
    with patch.dict('flask.current_app.config', {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY}):
        
        encrypted_data = encrypt_data(original_secret)
        decrypted_data = decrypt_data(encrypted_data)

    assert encrypted_data != original_secret
    assert decrypted_data == original_secret

def test_verify_2fa_token_correct(auth_service):
    """
    Verificar que 'verify_2fa_token' 
    devuelve True cuando el token es correcto.
    """
    secret = pyotp.random_base32()
    good_token = pyotp.TOTP(secret).now()
    
    mock_user = MagicMock()
    with patch.dict('flask.current_app.config', {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY}):
        mock_user.two_factor_secret = encrypt_data(secret)

    with patch.dict('flask.current_app.config', {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY}):
        is_valid = auth_service.verify_2fa_token(mock_user, good_token)

    assert is_valid is True

def test_verify_2fa_token_incorrect(auth_service):
    """
    Verificar que 'verify_2fa_token' 
    devuelve False cuando el token es incorrecto.
    """
    secret = pyotp.random_base32()
    bad_token = "000000"
    
    mock_user = MagicMock()
    with patch.dict('flask.current_app.config', {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY}):
        mock_user.two_factor_secret = encrypt_data(secret)

    with patch.dict('flask.current_app.config', {'ENCRYPTION_KEY': TEST_ENCRYPTION_KEY}):
        is_valid = auth_service.verify_2fa_token(mock_user, bad_token)

    assert is_valid is False

def test_generate_recovery_codes(auth_service):
    """
    Verificar que 'generate_recovery_codes'
    devuelve la estructura de datos correcta.
    """
    plain_codes, hashed_codes_json = auth_service.generate_recovery_codes()
    hashed_codes = json.loads(hashed_codes_json)

    assert isinstance(plain_codes, list)
    assert isinstance(hashed_codes, list)
    assert len(plain_codes) == 10
    assert len(hashed_codes) == 10
    assert len(plain_codes[0]) == 10

@patch('app.modules.auth.services.db.session.commit')
def test_verify_recovery_code_correct(mock_commit, auth_service):
    """
    Verificar que 'verify_recovery_code'
    devuelve True con un código válido y lo elimina de la lista.
    """
    plain_codes, hashed_codes_json = auth_service.generate_recovery_codes()
    
    mock_user = MagicMock()
    mock_user.two_factor_recovery_codes = hashed_codes_json
    
    is_valid = auth_service.verify_recovery_code(mock_user, plain_codes[3])
    
    assert is_valid is True
    mock_commit.assert_called_once()
    
    new_hashed_list = json.loads(mock_user.two_factor_recovery_codes)
    assert len(new_hashed_list) == 9 
    assert hashed_codes_json.count(json.loads(hashed_codes_json)[3]) == 1
    assert mock_user.two_factor_recovery_codes.count(json.loads(hashed_codes_json)[3]) == 0

@patch('app.modules.auth.services.db.session.commit')
def test_verify_recovery_code_incorrect(mock_commit, auth_service):
    """
    Verificar que 'verify_recovery_code'
    devuelve False con un código incorrecto.
    """
    _, hashed_codes_json = auth_service.generate_recovery_codes()
    
    mock_user = MagicMock()
    mock_user.two_factor_recovery_codes = hashed_codes_json
    
    is_valid = auth_service.verify_recovery_code(mock_user, "CODIGO-FALSO")
    
    assert is_valid is False
    mock_commit.assert_not_called()