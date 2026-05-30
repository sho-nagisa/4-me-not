from fastapi import Depends, FastAPI, Request
from sqlalchemy import text

from backend.app.account_context import (
    get_authenticated_account_id,
    reset_current_account_id,
    set_current_account_id,
)
from backend.app.api import auth, calendar, interaction, reference, reminder, search, task
from backend.app.http_security import add_security_headers, validate_csrf_request
from backend.app.security_config import validate_auth_configuration
from backend.db.session import engine
from backend.services.auth_service import SESSION_COOKIE_NAME, AuthService


app = FastAPI()

# Public router: registration, login, logout, and /me must stay reachable
# without an existing session.
app.include_router(auth.router, prefix="/api")

# Data routers require an authenticated account. The dependency returns 401 when
# no valid session is bound, and only falls back to DEFAULT_ACCOUNT_ID in dev.
authenticated = [Depends(get_authenticated_account_id)]
app.include_router(reference.router, prefix="/api", dependencies=authenticated)
app.include_router(interaction.router, prefix="/api", dependencies=authenticated)
app.include_router(reminder.router, prefix="/api", dependencies=authenticated)
app.include_router(search.router, prefix="/api", dependencies=authenticated)
app.include_router(task.router, prefix="/api", dependencies=authenticated)
app.include_router(calendar.router, prefix="/api", dependencies=authenticated)


@app.middleware("http")
async def bind_account_context(request: Request, call_next):
    csrf_response = validate_csrf_request(request)
    if csrf_response is not None:
        add_security_headers(csrf_response)
        return csrf_response

    # Binds the account context but never rejects a request, so public routes
    # (health, auth) stay reachable. Authorization is enforced per-router by the
    # get_authenticated_account_id dependency.
    service = AuthService()
    account_id = service.account_id_from_token(request.cookies.get(SESSION_COOKIE_NAME))
    context_token = None

    if account_id is not None and service.get_account(account_id) is not None:
        context_token = set_current_account_id(account_id)

    try:
        response = await call_next(request)
    finally:
        if context_token is not None:
            reset_current_account_id(context_token)
    add_security_headers(response, include_csp=request.url.path.startswith("/api/"))
    return response


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    validate_auth_configuration()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connection OK")
