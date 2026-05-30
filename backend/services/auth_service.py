from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException

from backend.app.security_config import auth_secret_key
from backend.db.session import db_session
from backend.models.account.account import Account
from backend.models.auth.login_attempt import LoginAttempt


SESSION_COOKIE_NAME = "forme_not_session"
SESSION_TTL_SECONDS = int(os.environ.get("AUTH_SESSION_TTL_SECONDS", "2592000"))
PASSWORD_ITERATIONS = int(os.environ.get("AUTH_PASSWORD_ITERATIONS", "260000"))
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthService:
    def register(self, email: str, password: str) -> Account:
        normalized_email = self._normalize_email(email)
        self._validate_password(password)

        with db_session() as db:
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

    def authenticate(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
    ) -> Account:
        normalized_email = self._normalize_email(email)
        self._enforce_login_rate_limit(normalized_email, ip_address)

        with db_session() as db:
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
                self._record_failed_login(normalized_email, ip_address)
                raise HTTPException(status_code=401, detail="Invalid email or password")
            self._clear_failed_login(normalized_email)
            return account

    def get_account(self, account_id: UUID) -> Account | None:
        with db_session() as db:
            account = db.get(Account, account_id)
            if account is None or not account.is_active:
                return None
            db.expunge(account)
            return account

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
        if not _EMAIL_PATTERN.fullmatch(normalized):
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
        return auth_secret_key()

    def _base64url_encode(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _base64url_decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}")

    def _enforce_login_rate_limit(self, email: str, ip_address: str | None) -> None:
        email_max = self._login_rate_limit_max_failures()
        ip_max = self._login_rate_limit_ip_max_failures()
        check_ip = ip_address is not None and ip_max > 0
        if email_max <= 0 and not check_ip:
            return

        cutoff = self._rate_limit_cutoff()
        with db_session() as db:
            if email_max > 0:
                email_failures = (
                    db.query(LoginAttempt)
                    .filter(
                        LoginAttempt.email == email,
                        LoginAttempt.created_at >= cutoff,
                    )
                    .count()
                )
                if email_failures >= email_max:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many failed login attempts",
                    )

            if check_ip:
                ip_failures = (
                    db.query(LoginAttempt)
                    .filter(
                        LoginAttempt.ip_address == ip_address,
                        LoginAttempt.created_at >= cutoff,
                    )
                    .count()
                )
                if ip_failures >= ip_max:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many failed login attempts",
                    )

    def _record_failed_login(self, email: str, ip_address: str | None) -> None:
        if (
            self._login_rate_limit_max_failures() <= 0
            and self._login_rate_limit_ip_max_failures() <= 0
        ):
            return

        with db_session() as db:
            # Opportunistic cleanup bounds the table to the active window so a
            # sustained attack cannot grow it without limit.
            db.query(LoginAttempt).filter(
                LoginAttempt.created_at < self._rate_limit_cutoff()
            ).delete(synchronize_session=False)
            db.add(LoginAttempt(email=email, ip_address=ip_address))
            db.commit()

    def _clear_failed_login(self, email: str) -> None:
        # Clears the email counter only; the IP counter persists so one valid
        # login cannot reset throttling for other accounts behind that IP.
        with db_session() as db:
            db.query(LoginAttempt).filter(
                LoginAttempt.email == email
            ).delete(synchronize_session=False)
            db.commit()

    def _rate_limit_cutoff(self) -> datetime:
        window_seconds = self._login_rate_limit_window_seconds()
        return datetime.now(timezone.utc) - timedelta(seconds=window_seconds)

    def _login_rate_limit_max_failures(self) -> int:
        return int(os.environ.get("AUTH_LOGIN_RATE_LIMIT_MAX_FAILURES", "5"))

    def _login_rate_limit_ip_max_failures(self) -> int:
        return int(os.environ.get("AUTH_LOGIN_RATE_LIMIT_IP_MAX_FAILURES", "20"))

    def _login_rate_limit_window_seconds(self) -> int:
        return int(os.environ.get("AUTH_LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))
