from fastapi import FastAPI
from sqlalchemy import text

from backend.app.api import interaction, reference, reminder
from backend.db.session import engine


app = FastAPI()

app.include_router(reference.router, prefix="/api")
app.include_router(interaction.router, prefix="/api")
app.include_router(reminder.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("DB connection OK")
