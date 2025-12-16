from locust import HttpUser, TaskSet, between, task


class FakenodoSafeBehavior(TaskSet):

    @task
    def create_and_publish_flow(self):
        deposition_id = None

        with self.client.post(
            "/api/deposit/depositions",
            json={"metadata": {"title": "Prueba Locust (Crea)"}},
            catch_response=True,
            name="/api/deposit/depositions (POST create)",
        ) as response:
            if response.status_code == 201:
                try:
                    deposition_id = response.json()["id"]
                    response.success()
                except Exception:
                    response.failure(f"Respuesta 201 pero JSON inválido. {response.text}")
            else:
                response.failure(f"Fallo al crear, status: {response.status_code}")
                return

        if deposition_id:
            with self.client.post(
                f"/api/deposit/depositions/{deposition_id}/actions/publish",
                catch_response=True,
                name="/api/deposit/depositions/ID/actions/publish (POST publish)",
            ) as response:
                if response.status_code == 202:
                    response.success()
                else:
                    response.failure(f"Fallo al publicar, status: {response.status_code}")


class FakenodoUser(HttpUser):
    tasks = [FakenodoSafeBehavior]
    wait_time = between(1, 3)

    host = "http://localhost:5000"
