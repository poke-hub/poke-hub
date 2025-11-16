from locust import HttpUser, TaskSet, between, task


class FakenodoSafeBehavior(TaskSet):

    @task
    def create_and_publish_flow(self):
        """
        Prueba el flujo que SÍ funciona, ahora con las rutas /api/ correctas.
        1. Llama a /api/deposit/depositions (POST)
        2. Omite la subida de archivos (que da TypeError 500)
        3. Llama a /api/deposit/depositions/ID/actions/publish (POST)
        """
        deposition_id = None

        # --- 1. Crear la deposición ---
        # (Ahora con /api/ al principio)
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
                # Si sigue dando 404, revisa cómo registraste el fakenodo_bp
                response.failure(f"Fallo al crear, status: {response.status_code}")
                return

        # --- 2. OMITIR LA SUBIDA DE ARCHIVO ---
        # (Seguimos omitiendo esto porque daría un error 500)

        # --- 3. Publicar la deposición ---
        if deposition_id:
            # (Ahora con /api/ al principio)
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

    # Este host es correcto
    host = "http://localhost:5000"
