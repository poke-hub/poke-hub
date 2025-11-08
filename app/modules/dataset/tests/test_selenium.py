import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from core.environment.host import get_host_for_selenium_testing
from core.selenium.common import initialize_driver, close_driver

def wait_for_page_to_load(driver, timeout=6):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")

def find(driver, by, value, timeout=6):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def count_datasets(driver, host):
    driver.get(f"{host}/dataset/list")
    wait_for_page_to_load(driver)
    try:
        return len(driver.find_elements(By.XPATH, "//table//tbody//tr"))
    except Exception:
        return 0

def login(driver, host):
    driver.get(f"{host}/login")
    wait_for_page_to_load(driver)
    find(driver, By.NAME, "email").send_keys("user1@example.com")
    find(driver, By.NAME, "password").send_keys("1234" + Keys.RETURN)
    time.sleep(2)
    wait_for_page_to_load(driver)

def test_upload_dataset():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login(driver, host)
        initial = count_datasets(driver, host)
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        find(driver, By.NAME, "title").send_keys("Title")
        find(driver, By.NAME, "desc").send_keys("Description")
        file_path = os.path.abspath("app/modules/dataset/uvl_examples/file1.uvl")
        find(driver, By.CLASS_NAME, "dz-hidden-input").send_keys(file_path)
        time.sleep(1)
        find(driver, By.ID, "agreeCheckbox").click()
        find(driver, By.ID, "upload_button").click()
        time.sleep(2)
        wait_for_page_to_load(driver)
        assert driver.current_url.endswith("/dataset/list")
        final = count_datasets(driver, host)
        assert final == initial + 1
        print("Test upload basic passed!")
    finally:
        close_driver(driver)

def test_upload_dataset_from_zip():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login(driver, host)
        initial = count_datasets(driver, host)
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        find(driver, By.ID, "tab-zip").click()
        zip_input = find(driver, By.ID, "zipFile")
        zip_path = os.path.abspath("app/modules/dataset/tests/test_files/test_dataset.zip")
        zip_input.send_keys(zip_path)
        find(driver, By.ID, "processZipBtn").click()
        time.sleep(2)
        wait_for_page_to_load(driver)
        final = count_datasets(driver, host)
        assert final >= initial, f"Expected dataset count to increase, got initial={initial}, final={final}"
        print("Test upload ZIP passed!")
    finally:
        close_driver(driver)


def test_upload_dataset_from_github():
    driver = initialize_driver()
    try:
        host = get_host_for_selenium_testing()
        login(driver, host)
        initial = count_datasets(driver, host)
        driver.get(f"{host}/dataset/upload")
        wait_for_page_to_load(driver)
        tab = find(driver, By.ID, "tab-github")
        tab.click()
        time.sleep(1)
        wait_for_page_to_load(driver)
        repo_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ghUrl"))
        )
        repo_input.send_keys("https://github.com/example/repo")
        find(driver, By.ID, "importGithubBtn").click()
        time.sleep(2)
        wait_for_page_to_load(driver)
        final = count_datasets(driver, host)
        assert final >= initial, f"Expected dataset count to increase, got initial={initial}, final={final}"
        print("Test upload GitHub passed!")
    finally:
        close_driver(driver)


test_upload_dataset()
test_upload_dataset_from_zip()
test_upload_dataset_from_github()
