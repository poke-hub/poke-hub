from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, between, task

from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):
    def on_start(self):
        self.login()

    def login(self):
        payload = {"email": "user1@example.com", "password": "1234"}
        self.client.post("/login", data=payload, name="/login")

    def get_csrf_token(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        token_tag = soup.find("input", {"name": "csrf_token"})
        return token_tag["value"] if token_tag else None

    @task
    def upload_zip(self):
        response = self.client.get("/dataset/upload")
        token = self.get_csrf_token(response)
        if not token:
            return
        files = {"zipFile": ("test.zip", b"fakecontent")}
        data = {"csrf_token": token}
        self.client.post("/dataset/zip/upload", data=data, files=files, name="/dataset/zip/upload")

    @task
    def upload_github(self):
        response = self.client.get("/dataset/upload")
        token = self.get_csrf_token(response)
        if not token:
            return
        data = {"csrf_token": token, "ghUrl": "https://github.com/example/repo"}
        self.client.post("/dataset/github/import", data=data, name="/dataset/github/import")

    @task
    def upload_basic(self):
        response = self.client.get("/dataset/upload")
        token = self.get_csrf_token(response)
        if not token:
            return
        data = {
            "csrf_token": token,
            "title": "Test dataset",
            "description": "Dataset de prueba",
            "tags": "test, locust",
        }
        self.client.post("/dataset/file/upload", data=data, name="/dataset/file/upload")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    wait_time = between(5, 9)
    host = get_host_for_locust_testing()
