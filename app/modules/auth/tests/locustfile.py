import pyotp
from locust import HttpUser, TaskSet, task

from core.environment.host import get_host_for_locust_testing
from core.locust.common import fake, get_csrf_token

KNOWN_2FA_SECRET = "5JEIF3ANYS7UJKZEN7PZJFG5RHTNRPR2"


class SignupBehavior(TaskSet):
    def on_start(self):
        self.signup()

    @task
    def signup(self):
        response = self.client.get("/signup")
        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/signup", data={"email": fake.email(), "password": fake.password(), "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Signup failed: {response.status_code}")


class LoginBehavior(TaskSet):
    def on_start(self):
        self.ensure_logged_out()
        self.login()

    @task
    def ensure_logged_out(self):
        response = self.client.get("/logout")
        if response.status_code != 200:
            print(f"Logout failed or no active session: {response.status_code}")

    @task
    def login(self):
        response = self.client.get("/login")
        if response.status_code != 200 or "Login" not in response.text:
            print("Already logged in or unexpected response, redirecting to logout")
            self.ensure_logged_out()
            response = self.client.get("/login")

        csrf_token = get_csrf_token(response)

        response = self.client.post(
            "/login", data={"email": "user1@example.com", "password": "1234", "csrf_token": csrf_token}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")


class TwoFactorLoginBehavior(TaskSet):
    """
    Simula el flujo de login completo de un usuario con 2FA activado.
    """

    def on_start(self):
        if KNOWN_2FA_SECRET != "5JEIF3ANYS7UJKZEN7PZJFG5RHTNRPR2":
            print("ERROR: KNOWN_2FA_SECRET is not set in locustfile.py.")
            self.user.stop()
            return
        self.totp = pyotp.TOTP(KNOWN_2FA_SECRET)
        self.email = "test@example.com"
        self.password = "test1234"
        self.client.get("/logout", name="/logout (2FA Setup)")

    @task
    def login_2fa_flow(self):
        """Ejecuta el flujo de login de 2 pasos."""

        csrf_token_A = None
        csrf_token_B = None

        with self.client.get("/login", name="/login (2FA Step 1 GET)", catch_response=True) as response_get_login:
            if response_get_login.status_code != 200:
                response_get_login.failure("Failed trying to GET /login")
                return
            csrf_token_A = get_csrf_token(response_get_login)

        with self.client.post(
            "/login",
            data={"email": self.email, "password": self.password, "csrf_token": csrf_token_A},
            allow_redirects=False,
            name="/login (2FA Step 1 POST)",
            catch_response=True,
        ) as response_post_login:
            if (
                response_post_login.status_code != 302
                or response_post_login.headers.get("Location") != "/login/verify-2fa"
            ):
                msg = (
                    "Step 1 (Password) failed. "
                    f"Expected 302 to /login/verify-2fa, got {response_post_login.status_code}"
                )
                response_post_login.failure(msg)
                return

        with self.client.get(
            "/login/verify-2fa", name="/login/verify-2fa (2FA Step 2 GET)", catch_response=True
        ) as response_get_verify:
            if response_get_verify.status_code != 200:
                response_get_verify.failure("Failed trying to GET /login/verify-2fa")
                return
            csrf_token_B = get_csrf_token(response_get_verify)

        token = self.totp.now()
        with self.client.post(
            "/login/verify-2fa",
            data={"token": token, "csrf_token": csrf_token_B},
            allow_redirects=False,
            name="/login/verify-2fa (2FA Step 2 POST)",
            catch_response=True,
        ) as response_post_verify:
            if response_post_verify.status_code != 302 or response_post_verify.headers.get("Location") != "/":
                msg = "Step 2 (Token) failed. " f"Expected 302 to /, got {response_post_verify.status_code}"
                response_post_verify.failure(msg)
                return

        self.client.get("/logout", name="/logout (2FA Cleanup)")


class AuthUser(HttpUser):
    tasks = {SignupBehavior: 1, LoginBehavior: 5, TwoFactorLoginBehavior: 5}
    min_wait = 5000
    max_wait = 9000
    host = get_host_for_locust_testing()
