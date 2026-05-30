import os


_DEV_ENVIRONMENTS = {"dev", "development", "local", "test"}
_DEV_AUTH_SECRET = "dev-auth-secret-change-me"
_PLACEHOLDER_AUTH_SECRETS = {
    "",
    _DEV_AUTH_SECRET,
    "change-this-local-secret",
    "replace-with-a-long-random-secret",
}
_MIN_PRODUCTION_SECRET_BYTES = 32


def app_environment() -> str:
    return os.environ.get("APP_ENV", "production").strip().lower()


def is_dev_environment() -> bool:
    return app_environment() in _DEV_ENVIRONMENTS


def auth_secret_key() -> bytes:
    secret = os.environ.get("AUTH_SECRET_KEY")
    if is_dev_environment():
        return (secret or _DEV_AUTH_SECRET).encode("utf-8")

    if secret is None or secret.strip() in _PLACEHOLDER_AUTH_SECRETS:
        raise RuntimeError(
            "AUTH_SECRET_KEY must be set to a unique non-placeholder value "
            "outside dev."
        )

    encoded = secret.encode("utf-8")
    if len(encoded) < _MIN_PRODUCTION_SECRET_BYTES:
        raise RuntimeError(
            "AUTH_SECRET_KEY must be at least 32 bytes outside dev."
        )
    return encoded


def auth_cookie_secure() -> bool:
    value = os.environ.get("AUTH_COOKIE_SECURE")
    if not is_dev_environment():
        return True
    if value is not None and value.strip():
        return value.strip().lower() == "true"
    return False


def validate_auth_configuration() -> None:
    if not is_dev_environment():
        auth_secret_key()
        if os.environ.get("AUTH_COOKIE_SECURE", "").strip().lower() == "false":
            raise RuntimeError(
                "AUTH_COOKIE_SECURE cannot be false outside dev."
            )
