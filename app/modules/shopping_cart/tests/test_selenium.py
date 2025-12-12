from selenium.webdriver.common.by import By
from core.selenium.common import initialize_driver, close_driver


class TestSeleniumRemoveCart():
  def setup_method(self, method):
    self.driver = initialize_driver()
    self.driver.implicitly_wait(10)
    self.vars = {}
  
  def teardown_method(self, method):
    close_driver(self.driver)

  def test_selenium_remove_cart(self):
    self.driver.get("http://127.0.0.1:5000/")
    self.driver.set_window_size(1706, 989)
    self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
    self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
    self.driver.find_element(By.ID, "password").send_keys("1234")
    self.driver.find_element(By.ID, "submit").click()
    self.driver.find_element(By.LINK_TEXT, "Sample dataset 4").click()
    self.driver.find_element(By.CSS_SELECTOR, ".navbar").click()
    self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
    self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
    self.driver.find_element(By.ID, "password").send_keys("1234")
    self.driver.find_element(By.ID, "submit").click()
    self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .d-flex a").click()
    self.driver.find_element(By.CSS_SELECTOR, ".row:nth-child(3) .btn-outline-success").click()
    self.driver.find_element(By.CSS_SELECTOR, ".nav-icon > .feather-shopping-cart").click()
    self.driver.find_element(By.LINK_TEXT, "Clear Cart").click()
    self.driver.find_element(By.LINK_TEXT, "Explore datasets").click()
    self.driver.find_element(By.LINK_TEXT, "Sample dataset 1").click()
    self.driver.find_element(By.CSS_SELECTOR, ".row:nth-child(2) > .col-12 > .btn-outline-success").click()
    self.driver.find_element(By.LINK_TEXT, "Add to cart").click()
    self.driver.find_element(By.CSS_SELECTOR, ".nav-item:nth-child(1) > .nav-icon").click()
    self.driver.find_element(By.LINK_TEXT, "Remove").click()
    self.driver.find_element(By.LINK_TEXT, "Remove").click()
  



class TestTestseleniumdownloadcart:
    def setup_method(self, method):
        self.driver = initialize_driver()
        self.driver.implicitly_wait(10)
        self.vars = {}

    def teardown_method(self, method):
        close_driver(self.driver)

    def test_testseleniumdownloadcart(self):
        self.driver.get("http://127.0.0.1:5000/")
        self.driver.set_window_size(1758, 805)
        self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.LINK_TEXT, "Upload dataset").click()
        self.driver.find_element(By.LINK_TEXT, "Explore").click()
        self.driver.find_element(By.LINK_TEXT, "Sample dataset 3").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-link:nth-child(1)").click()
        self.driver.find_element(By.ID, "email").send_keys("user1@example.com")
        self.driver.find_element(By.ID, "password").send_keys("1234")
        self.driver.find_element(By.ID, "submit").click()
        self.driver.find_element(By.CSS_SELECTOR, ".card:nth-child(1) .d-flex a").click()
        self.driver.find_element(By.LINK_TEXT, "Add to cart").click()
        self.driver.find_element(By.CSS_SELECTOR, ".row:nth-child(2) .btn-outline-success").click()
        self.driver.find_element(By.CSS_SELECTOR, ".nav-item:nth-child(1) > .nav-icon").click()
        self.driver.find_element(By.LINK_TEXT, "Descargar Todo").click()
