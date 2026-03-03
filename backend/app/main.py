from fastapi import FastAPI
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path

# ★ .env の場所を明示（プロジェクトルート）
# main.py は backend/app/main.py なので親を2回さかのぼると backend、
# さらにもう1階層上がプロジェクトルートになる。
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
# あるいは: load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from backend.app.api import interaction, reminder
from backend.db.session import engine

app = FastAPI()

app.include_router(interaction.router)
app.include_router(reminder.router)


@app.on_event("startup")
def on_startup():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ DB connection OK")
