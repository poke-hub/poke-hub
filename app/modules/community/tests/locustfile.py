import re
import time

from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, between, task

from core.environment.host import get_host_for_locust_testing


class CommunityBehavior(TaskSet):
    def get_csrf_token(self, response):
        soup = BeautifulSoup(response.text, "html.parser")
        token_tag = soup.find("input", {"name": "csrf_token"})
        return token_tag["value"] if token_tag else None

    def on_start(self):
        self.login()
        self.community_id = self.create_community()

    def login(self):
        # Usuario de pruebas presente en los seeds/test fixtures
        creds = {"email": "user@example.com", "password": "test1234"}
        self.client.post("/login", data=creds, name="/login")

    def create_community(self):
        # Obtiene CSRF y crea una comunidad única para este usuario
        resp = self.client.get("/community/create", name="/community/create (GET)")
        token = self.get_csrf_token(resp)
        if not token:
            return None

        name = f"Locust Community {int(time.time())}"
        data = {"csrf_token": token, "name": name, "description": "Comunidad creada por Locust"}

        with self.client.post(
            "/community/create",
            data=data,
            allow_redirects=False,
            catch_response=True,
            name="/community/create (POST)",
        ) as post_resp:
            if post_resp.status_code in (302, 303):
                location = post_resp.headers.get("Location", "")
                match = re.search(r"/community/view/([0-9]+)", location)
                if match:
                    post_resp.success()
                    return int(match.group(1))
                post_resp.failure(f"Redirect sin id de comunidad: {location}")
            else:
                post_resp.failure(f"Status inesperado al crear comunidad: {post_resp.status_code}")
        return None

    @task(2)
    def list_communities(self):
        self.client.get("/community/list", name="/community/list")

    @task(2)
    def view_created_community(self):
        if not self.community_id:
            return
        self.client.get(f"/community/view/{self.community_id}", name="/community/view/{id}")


class CommunityUser(HttpUser):
    tasks = [CommunityBehavior]
    wait_time = between(1, 3)
    host = get_host_for_locust_testing()
