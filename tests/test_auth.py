import os
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("AUTH_LOGIN_RATE_LIMIT_IP_MAX_FAILURES", "0")

from backend.app.main import app
from backend.app.http_security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from backend.app.security_config import auth_cookie_secure, validate_auth_configuration
from backend.db.session import SessionLocal
from backend.models.account.account import Account
from backend.models.auth.login_attempt import LoginAttempt
from backend.services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    AuthService,
)


class AuthAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.account_ids: list[str] = []
        self.login_attempt_emails: list[str] = []

    def tearDown(self) -> None:
        db = SessionLocal()
        try:
            if self.login_attempt_emails:
                db.query(LoginAttempt).filter(
                    LoginAttempt.email.in_(self.login_attempt_emails)
                ).delete(synchronize_session=False)
            for account_id in self.account_ids:
                account = db.get(Account, UUID(account_id))
                if account is not None:
                    db.delete(account)
            db.commit()
        finally:
            db.close()

    def _register(self, client: TestClient, email: str) -> dict:
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": "password123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.account_ids.append(payload["id"])
        return payload

    def test_register_login_me_and_logout(self) -> None:
        client = TestClient(app)
        email = f"auth-{uuid4().hex}@example.test"
        try:
            registered = self._register(client, email.upper())

            self.assertEqual(registered["email"], email)
            self.assertIn(SESSION_COOKIE_NAME, client.cookies)
            self.assertIn(CSRF_COOKIE_NAME, client.cookies)

            me = client.get("/api/auth/me")
            self.assertEqual(me.status_code, 200, me.text)
            self.assertEqual(me.json()["id"], registered["id"])

            logout = client.post("/api/auth/logout")
            self.assertEqual(logout.status_code, 200, logout.text)
            self.assertNotIn(SESSION_COOKIE_NAME, client.cookies)
            self.assertNotIn(CSRF_COOKIE_NAME, client.cookies)

            logged_out_me = client.get("/api/auth/me")
            self.assertEqual(logged_out_me.status_code, 401, logged_out_me.text)

            login = client.post(
                "/api/auth/login",
                json={"email": email, "password": "password123"},
            )
            self.assertEqual(login.status_code, 200, login.text)
            self.assertEqual(login.json()["id"], registered["id"])
            self.assertIn(CSRF_COOKIE_NAME, client.cookies)

            invalid_login = client.post(
                "/api/auth/login",
                json={"email": email, "password": "not-the-password"},
            )
            self.assertEqual(invalid_login.status_code, 401, invalid_login.text)
        finally:
            client.close()

    def test_security_headers_are_added_to_api_responses(self) -> None:
        client = TestClient(app)
        try:
            response = client.get("/api/health")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertEqual(response.headers["x-frame-options"], "DENY")
            self.assertEqual(response.headers["referrer-policy"], "no-referrer")
            self.assertEqual(
                response.headers["cross-origin-resource-policy"],
                "same-origin",
            )
            self.assertIn(
                "frame-ancestors 'none'",
                response.headers["content-security-policy"],
            )
        finally:
            client.close()

    def test_csrf_protection_rejects_authenticated_unsafe_requests(self) -> None:
        client = TestClient(app)
        email = f"auth-csrf-{uuid4().hex}@example.test"
        try:
            with patch.dict(
                os.environ,
                {"APP_ENV": "dev", "AUTH_CSRF_PROTECTION": "true"},
                clear=False,
            ):
                self._register(client, email)
                csrf_token = client.cookies.get(CSRF_COOKIE_NAME)
                self.assertIsNotNone(csrf_token)

                missing = client.post(
                    "/api/communities",
                    json={"name": f"csrf blocked {uuid4().hex}"},
                )
                self.assertEqual(missing.status_code, 403, missing.text)

                invalid = client.post(
                    "/api/communities",
                    json={"name": f"csrf invalid {uuid4().hex}"},
                    headers={CSRF_HEADER_NAME: "not-the-token"},
                )
                self.assertEqual(invalid.status_code, 403, invalid.text)

                created = client.post(
                    "/api/communities",
                    json={"name": f"csrf allowed {uuid4().hex}"},
                    headers={CSRF_HEADER_NAME: csrf_token},
                )
                self.assertEqual(created.status_code, 200, created.text)
        finally:
            client.close()

    def test_register_rejects_duplicate_email(self) -> None:
        client = TestClient(app)
        email = f"auth-duplicate-{uuid4().hex}@example.test"
        try:
            first = self._register(client, email)
            duplicate = client.post(
                "/api/auth/register",
                json={"email": email.upper(), "password": "password123"},
            )

            self.assertEqual(duplicate.status_code, 409, duplicate.text)
            self.assertEqual(first["email"], email)
        finally:
            client.close()

    def test_register_rejects_invalid_email_and_password_boundaries(self) -> None:
        client = TestClient(app)
        try:
            invalid_email = client.post(
                "/api/auth/register",
                json={"email": "not-an-email", "password": "password123"},
            )
            short_password = client.post(
                "/api/auth/register",
                json={"email": f"short-{uuid4().hex}@example.test", "password": "short"},
            )
            long_password = client.post(
                "/api/auth/register",
                json={
                    "email": f"long-{uuid4().hex}@example.test",
                    "password": "x" * 129,
                },
            )

            self.assertEqual(invalid_email.status_code, 400, invalid_email.text)
            self.assertEqual(short_password.status_code, 422, short_password.text)
            self.assertEqual(long_password.status_code, 422, long_password.text)
        finally:
            client.close()

    def test_session_token_rejects_tampering_and_expiration(self) -> None:
        service = AuthService()
        account = Account(
            id=uuid4(),
            email=f"token-{uuid4().hex}@example.test",
            is_active=True,
        )

        with patch("backend.services.auth_service.time.time", return_value=1000):
            token = service.create_session_token(account)

        payload_part, signature = token.rsplit(".", 1)
        tampered_signature = f"{signature[:-1]}{'A' if signature[-1] != 'A' else 'B'}"

        self.assertIsNone(service.account_id_from_token(f"{payload_part}.{tampered_signature}"))

        with patch(
            "backend.services.auth_service.time.time",
            return_value=1000 + SESSION_TTL_SECONDS + 1,
        ):
            self.assertIsNone(service.account_id_from_token(token))

    def test_production_requires_strong_auth_secret(self) -> None:
        service = AuthService()
        account = Account(
            id=uuid4(),
            email=f"secret-{uuid4().hex}@example.test",
            is_active=True,
        )

        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "AUTH_SECRET_KEY"):
                service.create_session_token(account)

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "AUTH_SECRET_KEY": "change-this-local-secret",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "AUTH_SECRET_KEY"):
                service.create_session_token(account)

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "AUTH_SECRET_KEY": "x" * 32,
            },
            clear=True,
        ):
            token = service.create_session_token(account)
            self.assertEqual(service.account_id_from_token(token), account.id)

    def test_auth_cookie_secure_defaults_to_production(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            self.assertTrue(auth_cookie_secure())

        with patch.dict(os.environ, {"APP_ENV": "dev"}, clear=True):
            self.assertFalse(auth_cookie_secure())

        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "AUTH_COOKIE_SECURE": "false",
            },
            clear=True,
        ):
            self.assertTrue(auth_cookie_secure())

    def test_production_rejects_insecure_cookie_configuration(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "AUTH_SECRET_KEY": "x" * 32,
                "AUTH_COOKIE_SECURE": "false",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "AUTH_COOKIE_SECURE"):
                validate_auth_configuration()

    def test_login_rate_limit_blocks_repeated_failures(self) -> None:
        client = TestClient(app)
        email = f"auth-rate-{uuid4().hex}@example.test"
        self.login_attempt_emails.append(email)
        try:
            with patch.dict(
                os.environ,
                {
                    "AUTH_LOGIN_RATE_LIMIT_MAX_FAILURES": "2",
                    "AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS": "300",
                },
                clear=False,
            ):
                self._register(client, email)

                for _ in range(2):
                    failed_login = client.post(
                        "/api/auth/login",
                        json={"email": email, "password": "wrong-password"},
                    )
                    self.assertEqual(failed_login.status_code, 401, failed_login.text)

                blocked_login = client.post(
                    "/api/auth/login",
                    json={"email": email, "password": "wrong-password"},
                )
                self.assertEqual(blocked_login.status_code, 429, blocked_login.text)
        finally:
            client.close()

    def test_login_rate_limit_blocks_repeated_failures_by_ip(self) -> None:
        client = TestClient(app)
        email = f"auth-rate-ip-{uuid4().hex}@example.test"
        # A unique forwarded IP isolates this test's IP counter from the constant
        # host TestClient reports for every other request.
        client_ip = f"198.51.100.{uuid4().int % 250 + 1}"
        headers = {"X-Forwarded-For": client_ip}
        self.login_attempt_emails.append(email)
        try:
            with patch.dict(
                os.environ,
                {
                    "AUTH_LOGIN_RATE_LIMIT_MAX_FAILURES": "0",
                    "AUTH_LOGIN_RATE_LIMIT_IP_MAX_FAILURES": "2",
                    "AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS": "300",
                },
                clear=False,
            ):
                self._register(client, email)

                for _ in range(2):
                    failed_login = client.post(
                        "/api/auth/login",
                        json={"email": email, "password": "wrong-password"},
                        headers=headers,
                    )
                    self.assertEqual(failed_login.status_code, 401, failed_login.text)

                blocked_login = client.post(
                    "/api/auth/login",
                    json={"email": email, "password": "wrong-password"},
                    headers=headers,
                )
                self.assertEqual(blocked_login.status_code, 429, blocked_login.text)
        finally:
            client.close()

    def test_authenticated_requests_use_account_scope(self) -> None:
        client_a = TestClient(app)
        client_b = TestClient(app)
        prefix = f"[AUTH:{uuid4().hex[:8]}]"
        try:
            self._register(client_a, f"{prefix.lower()}-a@example.test")
            self._register(client_b, f"{prefix.lower()}-b@example.test")

            community = client_a.post(
                "/api/communities",
                json={"name": f"{prefix} private community"},
            )
            self.assertEqual(community.status_code, 200, community.text)

            person = client_a.post(
                "/api/persons",
                json={
                    "name": f"{prefix} private person",
                    "canonical_name": f"{prefix}:private-person",
                    "primary_community_id": community.json()["id"],
                },
            )
            self.assertEqual(person.status_code, 200, person.text)

            people_a = client_a.get("/api/persons")
            people_b = client_b.get("/api/persons")
            self.assertEqual(people_a.status_code, 200, people_a.text)
            self.assertEqual(people_b.status_code, 200, people_b.text)

            person_id = person.json()["id"]
            self.assertTrue(any(item["id"] == person_id for item in people_a.json()))
            self.assertFalse(any(item["id"] == person_id for item in people_b.json()))
        finally:
            client_a.close()
            client_b.close()

    def test_protected_endpoints_reject_unauthenticated_requests_in_production(
        self,
    ) -> None:
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            client = TestClient(app)
            try:
                self.assertEqual(client.get("/api/health").status_code, 200)

                for path in ("/api/persons", "/api/interactions", "/api/tasks"):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 401, f"{path}: {response.text}")

                search = client.get("/api/search", params={"q": "anything"})
                self.assertEqual(search.status_code, 401, search.text)

                created = client.post(
                    "/api/persons",
                    json={"name": "should not be created"},
                )
                self.assertEqual(created.status_code, 401, created.text)
            finally:
                client.close()

    def test_protected_endpoints_allow_unauthenticated_requests_in_dev(self) -> None:
        with patch.dict(os.environ, {"APP_ENV": "dev"}, clear=False):
            client = TestClient(app)
            try:
                response = client.get("/api/persons")
                self.assertEqual(response.status_code, 200, response.text)
            finally:
                client.close()

    def test_search_results_do_not_cross_account_boundary(self) -> None:
        client_a = TestClient(app)
        client_b = TestClient(app)
        prefix = f"[AUTH-SEARCH:{uuid4().hex[:8]}]"
        try:
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
                self._register(client_a, f"{prefix.lower()}-a@example.test")
                self._register(client_b, f"{prefix.lower()}-b@example.test")

                community = client_a.post(
                    "/api/communities",
                    json={"name": f"{prefix} private community"},
                )
                self.assertEqual(community.status_code, 200, community.text)

                person = client_a.post(
                    "/api/persons",
                    json={
                        "name": f"{prefix} private person",
                        "canonical_name": f"{prefix}:private-person",
                        "primary_community_id": community.json()["id"],
                    },
                )
                self.assertEqual(person.status_code, 200, person.text)

                interaction = client_a.post(
                    "/api/interactions",
                    json={
                        "person_id": person.json()["id"],
                        "community_id": community.json()["id"],
                        "interaction_type": "MEETING",
                        "share_level": "SHARED",
                        "content": f"{prefix} account-private-search-token",
                        "note": f"{prefix} private note",
                    },
                )
                self.assertEqual(interaction.status_code, 200, interaction.text)

                params = {
                    "q": "account-private-search-token",
                    "target_type": "interaction",
                }
                search_a = client_a.get("/api/search", params=params)
                search_b = client_b.get("/api/search", params=params)

                self.assertEqual(search_a.status_code, 200, search_a.text)
                self.assertEqual(search_b.status_code, 200, search_b.text)
                self.assertTrue(search_a.json()["results"])
                self.assertEqual(search_b.json()["results"], [])
        finally:
            client_a.close()
            client_b.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
