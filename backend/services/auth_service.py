from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.models.account.account import Account


SESSION_COOKIE_NAME = "forme_not_session"
SESSION_TTL_SECONDS = int(os.environ.get("AUTH_SESSION_TTL_SECONDS", "2592000"))
PASSWORD_ITERATIONS = int(os.environ.get("AUTH_PASSWORD_ITERATIONS", "260000"))


class AuthService:
    def register(self, email: str, password: str) -> Account:
        normalized_email = self._normalize_email(email)
        self._validate_password(password)

        db: Session = SessionLocal()
        try:
            existing = (
                db.query(Account)
                .filter(Account.email == normalized_email)
                .first()
            )
            if existing is not None:
                raise HTTPException(status_code=409, detail="Account already exists")

            account = Account(
                email=normalized_email,
                password_hash=self.hash_password(password),
                is_active=True,
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            return account
        finally:
            db.close()

    def authenticate(self, email: str, password: str) -> Account:
        normalized_email = self._normalize_email(email)
        db: Session = SessionLocal()
        try:
            account = (
                db.query(Account)
                .filter(Account.email == normalized_email)
                .first()
            )
            if (
                account is None
                or not account.is_active
                or not account.password_hash
                or not self.verify_password(password, account.password_hash)
            ):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            return account
        finally:
            db.close()

    def get_account(self, account_id: UUID) -> Account | None:
        db: Session = SessionLocal()
        try:
            account = db.get(Account, account_id)
            if account is None or not account.is_active:
                return None
            db.expunge(account)
            return account
        finally:
            db.close()

    def create_session_token(self, account: Account) -> str:
        payload = {
            "sub": str(account.id),
            "exp": int(time.time()) + SESSION_TTL_SECONDS,
        }
        payload_text = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        payload_part = self._base64url_encode(payload_text)
        signature = self._sign(payload_part)
        return f"{payload_part}.{signature}"

    def account_id_from_token(self, token: str | None) -> UUID | None:
        if not token or "." not in token:
            return None

        payload_part, signature = token.rsplit(".", 1)
        expected_signature = self._sign(payload_part)
        if not hmac.compare_digest(signature, expected_signature):
            return None

        try:
            payload = json.loads(self._base64url_decode(payload_part))
            expires_at = int(payload.get("exp", 0))
            if expires_at < int(time.time()):
                return None
            return UUID(str(payload["sub"]))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def hash_password(self, password: str) -> str:
        salt = secrets.token_urlsafe(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PASSWORD_ITERATIONS,
        )
        return (
            f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}$"
            f"{self._base64url_encode(digest)}"
        )

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt, expected_digest = password_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations_text),
            )
            actual_digest = self._base64url_encode(digest)
            return hmac.compare_digest(actual_digest, expected_digest)
        except (ValueError, TypeError):
            return False

    def serialize_account(self, account: Account) -> dict:
        return {
            "id": str(account.id),
            "email": account.email,
            "is_active": bool(account.is_active),
        }

    def _normalize_email(self, email: str) -> str:
        normalized = email.strip().lower()
        if not normalized or "@" not in normalized:
            raise HTTPException(status_code=400, detail="Email is invalid")
        if len(normalized) > 255:
            raise HTTPException(status_code=400, detail="Email is too long")
        return normalized

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password is too short")
        if len(password) > 128:
            raise HTTPException(status_code=400, detail="Password is too long")

    def _sign(self, payload_part: str) -> str:
        digest = hmac.new(
            self._secret_key(),
            payload_part.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return self._base64url_encode(digest)

    def _secret_key(self) -> bytes:
        return os.environ.get("AUTH_SECRET_KEY", "dev-auth-secret-change-me").encode(
            "utf-8"
        )

    def _base64url_encode(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _base64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}")
