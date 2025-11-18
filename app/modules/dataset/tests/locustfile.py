from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, between, task

from core.environment.host import get_host_for_locust_testing


class DatasetBehavior(TaskSet):

    def get_csrf_token(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        token_tag = soup.find("input", {"name": "csrf_token"})
        return token_tag["value"] if token_tag else None

    def on_start(self):

        login_data = {
            "email": "user@example.com",
            "password": "test1234"
        }
        self.client.post("/login", data=login_data)

        response = self.client.get("/dataset/upload")
        self.csrf_token = self.get_csrf_token(response)

        data = {
            "csrf_token": self.csrf_token,
            "save_as_draft": "true",
            "title": f"Draft Locust {int(time.time())}",
            "desc": "Borrador creado por Locust",
            "publication_type": "article",
            "tags": "loadtest,locust"
        }

        create_resp = self.client.post("/dataset/upload", data=data)
        if create_resp.status_code == 200 and b"dataset_id" in create_resp.content:
            self.dataset_id = create_resp.json().get("dataset_id")
        else:
            self.dataset_id = None
            print(f"⚠️ No se pudo crear el dataset draft: {create_resp.status_code}")

    @task(2)
    def edit_draft_dataset(self):

        if not self.dataset_id:
            return

        response = self.client.get(f"/dataset/{self.dataset_id}/edit")
        csrf_token = self.get_csrf_token(response)

        data = {
            "csrf_token": csrf_token,
            "save_as_draft": "true",
            "title": f"Draft actualizado {random.randint(1, 1000)}",
            "desc": "desc",
            "publication_type": "article",
            "tags": "update,locust"
        }

        with self.client.post(f"/dataset/{self.dataset_id}/edit", data=data, catch_response=True) as resp:
            if resp.status_code in (200, 302) and b"Draft updated" in resp.content:
                resp.success()
            else:
                resp.failure(f"Error editing draft {self.dataset_id}: {resp.status_code}")

    @task(1)
    def view_upload_page(self):

        self.client.get("/dataset/upload")
        self.login()

    def login(self):
        payload = {"email": "user1@example.com", "password": "1234"}
        self.client.post("/login", data=payload, name="/login")

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

    @task
    def download_dataset(self):
        dataset_id = 1
        self.client.get(f"/dataset/download/{dataset_id}")


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    wait_time = between(5, 9)
    host = get_host_for_locust_testing()
