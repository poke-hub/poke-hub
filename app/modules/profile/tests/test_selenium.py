import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.modules.auth.models import UserSession, User
from app import db
from core.selenium.common import initialize_driver

@pytest.fixture(scope="function")
def driver():
    """
    Fixture para inicializar y finalizar el driver de Selenium.
    Usa la configuración centralizada del proyecto (initialize_driver).
    """
    driver = initialize_driver()
    yield driver
    driver.quit()

def test_view_and_revoke_sessions(driver, test_client):
    """
    Test de integración con Selenium:
    1. Login.
    2. Crear sesión remota falsa en BBDD (para tener algo que revocar).
    3. Ir a perfil/seguridad.
    4. Verificar que aparece y revocarla.
    """
    # -----------------------------------------------------------------------
    # 1. LOGIN
    # -----------------------------------------------------------------------
    user_email = "user_selenium@example.com"
    user_pass = "1234"
    
    with test_client.application.app_context():
        if not User.query.filter_by(email=user_email).first():
            user = User(email=user_email, password=user_pass)
            db.session.add(user)
            db.session.commit()

    driver.get("http://localhost:5000/login")
    
    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_field.send_keys(user_email)
    driver.find_element(By.NAME, "password").send_keys(user_pass)
    driver.find_element(By.ID, "submit").click()
    
    # Esperar redirección al index
    WebDriverWait(driver, 10).until(EC.url_contains("/"))

    # -----------------------------------------------------------------------
    # 2. INYECTAR SESIÓN FALSA
    # -----------------------------------------------------------------------
    fake_device_name = "Firefox Remote Selenium"
    
    with test_client.application.app_context():
        user = User.query.filter_by(email=user_email).first()
        fake_session = UserSession(
            user_id=user.id,
            token="fake_token_remote_selenium",
            ip_address="10.0.0.99",
            device=fake_device_name,
            last_seen=db.func.now()
        )
        db.session.add(fake_session)
        db.session.commit()
        fake_session_id = fake_session.id

    # -----------------------------------------------------------------------
    # 3. IR A SECURITY SETTINGS Y VERIFICAR
    # -----------------------------------------------------------------------
    driver.get("http://localhost:5000/profile/security")

    # Verificar que existe la sesión remota en la tabla
    WebDriverWait(driver, 10).until(
        EC.text_to_be_present_in_element((By.TAG_NAME, "body"), fake_device_name)
    )
    
    # -----------------------------------------------------------------------
    # 4. REVOCAR SESIÓN
    # -----------------------------------------------------------------------
    # Buscar el botón de revocar asociado a la sesión falsa
    revoke_btn = driver.find_element(By.XPATH, f"//form[contains(@action, '/revoke/{fake_session_id}')]/button")
    revoke_btn.click()

    # -----------------------------------------------------------------------
    # 5. VERIFICAR RESULTADO
    # -----------------------------------------------------------------------
    success_msg = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
    )
    assert "Session revoked successfully" in success_msg.text
    
    # Verificar que desapareció de la lista
    assert fake_device_name not in driver.page_source

    # Limpieza final
    with test_client.application.app_context():
        UserSession.query.filter_by(id=fake_session_id).delete()
        u = User.query.filter_by(email=user_email).first()
        if u:
            db.session.delete(u)
        db.session.commit()