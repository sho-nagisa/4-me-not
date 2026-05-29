import os
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.db.session import SessionLocal
from backend.models.account.account import Account
from backend.services.auth_service import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    AuthService,
)


class AuthAPITest(unittest.TestCase):
    def setUp(self) -> None:
        self.account_ids: list[str] = []

    def tearDown(self) -> None:
        db = SessionLocal()
        try:
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

            me = client.get("/api/auth/me")
            self.assertEqual(me.status_code, 200, me.text)
            self.assertEqual(me.json()["id"], registered["id"])

            logout = client.post("/api/auth/logout")
            self.assertEqual(logout.status_code, 200, logout.text)
            self.assertNotIn(SESSION_COOKIE_NAME, client.cookies)

            logged_out_me = client.get("/api/auth/me")
            self.assertEqual(logged_out_me.status_code, 401, logged_out_me.text)

            login = client.post(
                "/api/auth/login",
                json={"email": email, "password": "password123"},
            )
            self.assertEqual(login.status_code, 200, login.text)
            self.assertEqual(login.json()["id"], registered["id"])

            invalid_login = client.post(
                "/api/auth/login",
                json={"email": email, "password": "not-the-password"},
            )
            self.assertEqual(invalid_login.status_code, 401, invalid_login.text)
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
