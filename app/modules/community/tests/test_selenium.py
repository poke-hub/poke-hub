import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import db
from app.modules.auth.models import User
from app.modules.community.models import Community
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver


@pytest.fixture(scope="function")
def driver():
    drv = initialize_driver()
    yield drv
    drv.quit()


def _cleanup(email, community_name, app):
    with app.app_context():
        comm = Community.query.filter_by(name=community_name).first()
        if comm:
            db.session.delete(comm)
        user = User.query.filter_by(email=email).first()
        if user:
            db.session.delete(user)
        db.session.commit()


def test_create_community_via_ui(driver, test_client):
    host = get_host_for_selenium_testing()
    timestamp = int(time.time())
    email = f"community_selenium_{timestamp}@example.com"
    password = "1234"
    community_name = f"Community Selenium {timestamp}"

    # Sign up to ensure valid user in the same DB the app is using
    driver.get(f"{host}/signup/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name"))).send_keys("Test")
    driver.find_element(By.NAME, "surname").send_keys("Selenium")
    driver.find_element(By.NAME, "email").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    # Submit the form (input submit rendered by WTForms)
    signup_submit = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form input[type='submit'], form button[type='submit']"))
    )
    signup_submit.click()
    WebDriverWait(driver, 10).until(lambda d: "signup" not in d.current_url)

    # Go to create community
    driver.get(f"{host}/community/create")
    name_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
    name_input.send_keys(community_name)
    desc_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='description']"))
    )
    desc_input.send_keys("Created via Selenium test")
    submit_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "form button[type='submit'], form input[type='submit']"))
    )
    submit_btn.click()

    # Expect redirect to view page with name present
    WebDriverWait(driver, 10).until(EC.url_contains("/community/view/"))
    WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), community_name))

    _cleanup(email, community_name, test_client.application)
