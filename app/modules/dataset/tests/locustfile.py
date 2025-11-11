from locust import HttpUser, TaskSet, task, between

from core.environment.host import get_host_for_locust_testing
from core.locust.common import get_csrf_token


class DatasetBehavior(TaskSet):
    def on_start(self):

        login_data = {
            "email": "user@example.com",
            "password": "test1234"
        }
        self.client.post("/login", data=login_data)

        response = self.client.get("/dataset/upload")
        self.csrf_token = get_csrf_token(response)

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
        csrf_token = get_csrf_token(response)

        data = {
            "csrf_token": csrf_token,
            "save_as_draft": "true",
            "title": f"Draft actualizado {random.randint(1,1000)}",
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


class DatasetUser(HttpUser):
    tasks = [DatasetBehavior]
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
