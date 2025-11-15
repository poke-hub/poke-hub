from locust import HttpUser, TaskSet, between, task


class FakenodoBehavior(TaskSet):

    @task
    def create_publish_flow(self):
        deposition_id = None

        with self.client.post(
            "/api/deposit/depositions",
            json={"metadata": {"title": "Dataset de prueba con Locust"}},
            catch_response=True,
            name="/api/deposit/depositions (POST)",
        ) as response:
            if response.status_code == 201:
                deposition_id = response.json()["id"]
                response.success()
            else:
                response.failure(f"Failed to create deposition, status: {response.status_code}")
                return

        if deposition_id:
            file_content = b"Este es el contenido de un archivo de prueba generado por Locust."
            files = {"file": ("test_file.txt", file_content, "text/plain")}
            with self.client.post(
                f"/api/deposit/depositions/{deposition_id}/files",
                files=files,
                catch_response=True,
                name="/api/deposit/depositions/ID/files (POST)",
            ) as response:
                if response.status_code == 201:
                    response.success()
                else:
                    response.failure(f"Failed to upload file, status: {response.status_code}")
                    return
        if deposition_id:
            with self.client.post(
                f"/api/deposit/depositions/{deposition_id}/actions/publish",
                catch_response=True,
                name="/api/deposit/depositions/ID/actions/publish (POST)",
            ) as response:
                if response.status_code in [200, 202]:
                    response.success()
                else:
                    response.failure(f"Failed to publish deposition, status: {response.status_code}")


class FakenodoUser(HttpUser):
    tasks = [FakenodoBehavior]

    wait_time = between(10, 30)

    host = "http://localhost:5000"
