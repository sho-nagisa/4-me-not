from fastapi import FastAPI, Request
from sqlalchemy import text

from backend.app.account_context import reset_current_account_id, set_current_account_id
from backend.app.api import auth, calendar, interaction, reference, reminder, search, task
from backend.db.session import engine
from backend.services.auth_service import SESSION_COOKIE_NAME, AuthService


app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(reference.router, prefix="/api")
app.include_router(interaction.router, prefix="/api")
app.include_router(reminder.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(task.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")


@app.middleware("http")
async def bind_account_context(request: Request, call_next):
    service = AuthService()
    account_id = service.account_id_from_token(request.cookies.get(SESSION_COOKIE_NAME))
    context_token = None

    if account_id is not None and service.get_account(account_id) is not None:
        context_token = set_current_account_id(account_id)

    try:
        return await call_next(request)
    finally:
        if context_token is not None:
            reset_current_account_id(context_token)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connection OK")
