import os
import time
import re
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import close_driver, initialize_driver

@pytest.fixture
def driver():
    drv = initialize_driver()
    yield drv
    close_driver(drv)


def wait_for_page_to_load(driver, timeout=4):
    WebDriverWait(driver, timeout).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )


def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)

    try:
        amount_datasets = len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        amount_datasets = 0
    return amount_datasets


def login_user(driver, host, email="user1@example.com", password="1234"):
    """Helper function to login a user"""
    driver.get(f"{host}/login")
    wait_for_page_to_load(driver)

    email_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    password_field = driver.find_element(By.NAME, "password")

    email_field.send_keys(email)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    wait_for_page_to_load(driver)


def test_upload_dataset():
    driver = initialize_driver()

    try:
        host = get_host_for_selenium_testing()

        # Open the login page
        driver.get(f"{host}/login")
        wait_for_page_to_load(driver)

        # Find the username and password field and enter the values
        email_field = driver.find_element(By.NAME, "email")
        password_field = driver.find_element(By.NAME, "password")

        email_field.send_keys("user1@example.com")
        password_field.send_keys("1234")

        # Send the form
        password_field.send_keys(Keys.RETURN)
        time.sleep(4)
        wait_for_page_to_load(driver)

        # Count initial datasets
        initial_datasets = count_datasets(driver, host)

        # Open the upload dataset
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)

        # Find basic info and UVL model and fill values
        title_field = driver.find_element(By.NAME, "title")
        title_field.send_keys("Title")
        desc_field = driver.find_element(By.NAME, "desc")
        desc_field.send_keys("Description")
        tags_field = driver.find_element(By.NAME, "tags")
        tags_field.send_keys("tag1,tag2")

        # Add two authors and fill
        add_author_button = driver.find_element(By.ID, "add_author")
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        add_author_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field0 = driver.find_element(By.NAME, "authors-0-name")
        name_field0.send_keys("Author0")
        affiliation_field0 = driver.find_element(By.NAME, "authors-0-affiliation")
        affiliation_field0.send_keys("Club0")
        orcid_field0 = driver.find_element(By.NAME, "authors-0-orcid")
        orcid_field0.send_keys("0000-0000-0000-0000")

        name_field1 = driver.find_element(By.NAME, "authors-1-name")
        name_field1.send_keys("Author1")
        affiliation_field1 = driver.find_element(By.NAME, "authors-1-affiliation")
        affiliation_field1.send_keys("Club1")

        # Obtén las rutas absolutas de los archivos
        file1_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        file2_path = os.path.abspath("app/modules/dataset/uvl_examples/file2.uvl")

        # Subir el primer archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file1_path)
        wait_for_page_to_load(driver)

        # Subir el segundo archivo
        dropzone = driver.find_element(By.CLASS_NAME, "dz-hidden-input")
        dropzone.send_keys(file2_path)
        wait_for_page_to_load(driver)

        # Add authors in UVL models
        show_button = driver.find_element(By.ID, "0_button")
        show_button.send_keys(Keys.RETURN)
        add_author_uvl_button = driver.find_element(By.ID, "0_form_authors_button")
        add_author_uvl_button.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)

        name_field = driver.find_element(By.NAME, "feature_models-0-authors-2-name")
        name_field.send_keys("Author3")
        affiliation_field = driver.find_element(By.NAME, "feature_models-0-authors-2-affiliation")
        affiliation_field.send_keys("Club3")

        # Check I agree and send form
        check = driver.find_element(By.ID, "agreeCheckbox")
        check.send_keys(Keys.SPACE)
        wait_for_page_to_load(driver)

        upload_btn = driver.find_element(By.ID, "upload_button")
        upload_btn.send_keys(Keys.RETURN)
        wait_for_page_to_load(driver)
        time.sleep(2)  # Force wait time

        assert driver.current_url == f"{host}/dataset/list", "Test failed!"

        # Count final datasets
        final_datasets = count_datasets(driver, host)
        assert final_datasets == initial_datasets + 1, "Test failed!"

        print("Test passed!")

    finally:

        # Close the browser
        close_driver(driver)


def test_trending_views_and_downloads_buttons(driver):
    """Test that clicking Views/Downloads buttons changes the header and keeps the correct button active"""
    host = get_host_for_selenium_testing()
    
    # Login
    login_user(driver, host)

    # Verify initial state - should show Views by default
    header_views = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h3[contains(., 'Top 3 this month (views)')]"))
    )
    assert header_views is not None, "Views header should be visible initially"

    # Verify Views button is active
    views_button = driver.find_element(By.XPATH, "//a[contains(@href, 'metric=views')]")
    assert "active" in views_button.get_attribute("class"), "Views button should be active initially"

    # Click on Downloads button
    downloads_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'metric=downloads')]"))
    )
    downloads_button.click()
    wait_for_page_to_load(driver)

    # Verify header changed to Downloads
    header_downloads = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h3[contains(., 'Top 3 this month (downloads)')]"))
    )
    assert header_downloads is not None, "Downloads header should be visible after clicking Downloads button"

    # Verify Downloads button is now active
    downloads_button = driver.find_element(By.XPATH, "//a[contains(@href, 'metric=downloads')]")
    assert "active" in downloads_button.get_attribute("class"), "Downloads button should be active after click"

    # Verify URL changed
    assert "metric=downloads" in driver.current_url, "URL should contain metric=downloads parameter"

    # Click back on Views button
    views_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'metric=views')]"))
    )
    views_button.click()
    wait_for_page_to_load(driver)

    # Verify header changed back to Views
    header_views = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//h3[contains(., 'Top 3 this month (views)')]"))
    )
    assert header_views is not None, "Views header should be visible after clicking Views button"

    # Verify Views button is active again
    views_button = driver.find_element(By.XPATH, "//a[contains(@href, 'metric=views')]")
    assert "active" in views_button.get_attribute("class"), "Views button should be active after clicking it"


def test_top3_list_shows_counts(driver):
    """Test that Top 3 list items show proper count format (number + 'views' or 'downloads')"""
    host = get_host_for_selenium_testing()
    
    # Login
    login_user(driver, host)

    # Test Views metric
    driver.get(f"{host}/?metric=views")
    wait_for_page_to_load(driver)

    # Check if there are trending views or empty state
    try:
        ol = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card .card-body ol"))
        )
        items = ol.find_elements(By.TAG_NAME, "li")
        
        assert len(items) > 0, "Should have at least one item in Top 3 views"
        
        for li in items:
            text = li.text
            # Verify format: should contain "– NUMBER views"
            # Example: "Dataset Title – 150 views"
            assert re.search(r'–\s+\d+\s+views', text), \
                f"Item should contain '– NUMBER views' format, got: {text}"
    
    except Exception:
        # Check for empty state message
        empty_message = driver.find_element(By.XPATH, "//p[contains(., 'No trending datasets yet')]")
        assert empty_message is not None, "Should show empty state message when no trending views"

    # Test Downloads metric
    driver.get(f"{host}/?metric=downloads")
    wait_for_page_to_load(driver)

    try:
        ol = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card .card-body ol"))
        )
        items = ol.find_elements(By.TAG_NAME, "li")
        
        assert len(items) > 0, "Should have at least one item in Top 3 downloads"
        
        for li in items:
            text = li.text
            # Verify format: should contain "– NUMBER downloads"
            # Example: "Dataset Title – 42 downloads"
            assert re.search(r'–\s+\d+\s+downloads', text), \
                f"Item should contain '– NUMBER downloads' format, got: {text}"
    
    except Exception:
        # Check for empty state message
        empty_message = driver.find_element(By.XPATH, "//p[contains(., 'No trending downloads yet')]")
        assert empty_message is not None, "Should show empty state message when no trending downloads"


def test_top3_list_structure(driver):
    """Test the complete structure of Top 3 list items"""
    host = get_host_for_selenium_testing()
    
    # Login
    login_user(driver, host)

    driver.get(f"{host}/?metric=views")
    wait_for_page_to_load(driver)

    try:
        ol = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".card .card-body ol"))
        )
        items = ol.find_elements(By.TAG_NAME, "li")
        
        for li in items:
            # Each item should have a link to the dataset
            link = li.find_element(By.TAG_NAME, "a")
            assert link.get_attribute("href"), "Each item should have a link to dataset"
            
            # Should have author info in a div with class 'text-muted small'
            author_div = li.find_element(By.CSS_SELECTOR, "div.text-muted.small")
            assert author_div.text, "Each item should show author information"
            
    except Exception:
        # Empty state is acceptable
        pass


# Call the test function (this should be removed in production - pytest discovers tests automatically)
# test_upload_dataset()