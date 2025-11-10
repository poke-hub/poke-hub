from selenium import webdriver
from selenium.webdriver.common.by import By


class Test3:

    def setup_method(self, method):
        self.driver = webdriver.Firefox()
        self.vars = {}

    def teardown_method(self, method):
        self.driver.quit()

    def test_3(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1014, 754)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
        self.driver.find_element(By.LINK_TEXT, "Add to cart").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn-close:nth-child(1)").click()
        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(4) .btn-outline-success").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-icon > .feather-shopping-cart").click()
        self.driver.find_element(By.LINK_TEXT, "Remove").click()
        self.driver.find_element(By.LINK_TEXT, "Vaciar Carrito").click()
        self.driver.find_element(By.CSS_SELECTOR, ".btn-close:nth-child(1)").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-item:nth-child(1) > .nav-icon").click()
        self.driver.find_element(By.LINK_TEXT, "My datasets").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 1").click()
        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(4) .btn-outline-success").click()
        self.driver.find_element(By.CSS_SELECTOR, ".list-group-item:nth-child(4) .btn-outline-success").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-icon > .feather-shopping-cart").click()
        self.driver.find_element(By.LINK_TEXT, "Vaciar Carrito").click()
        self.driver.find_element(By.CSS_SELECTOR, ".text-dark").click()
