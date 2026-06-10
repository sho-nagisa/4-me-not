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
_DEV_TRUSTED_HOSTS = ("localhost", "127.0.0.1", "testserver", "*.localhost")
_DEV_CORS_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


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


def trusted_hosts() -> list[str]:
    configured = _split_csv_env("APP_TRUSTED_HOSTS")
    if configured:
        return configured
    if is_dev_environment():
        return list(_DEV_TRUSTED_HOSTS)
    return []


def cors_allowed_origins() -> list[str]:
    configured = _split_csv_env("APP_CORS_ALLOWED_ORIGINS")
    if configured:
        return configured
    if is_dev_environment():
        return list(_DEV_CORS_ALLOWED_ORIGINS)
    return []


def validate_auth_configuration() -> None:
    if not is_dev_environment():
        auth_secret_key()
        if os.environ.get("AUTH_COOKIE_SECURE", "").strip().lower() == "false":
            raise RuntimeError(
                "AUTH_COOKIE_SECURE cannot be false outside dev."
            )
        hosts = trusted_hosts()
        if not hosts or "*" in hosts:
            raise RuntimeError(
                "APP_TRUSTED_HOSTS must be set to explicit host names outside dev."
            )
        if "*" in cors_allowed_origins():
            raise RuntimeError(
                "APP_CORS_ALLOWED_ORIGINS cannot contain '*' outside dev."
            )


def _split_csv_env(name: str) -> list[str]:
    value = os.environ.get(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]
