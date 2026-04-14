import logging
import time
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app import models  # noqa: F401
from app.api.routes import router
from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.grouping import run_grouping_cycle

logger = logging.getLogger(__name__)


def wait_for_database(max_retries: int = 20, delay_seconds: int = 2) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == max_retries:
                raise
            logger.warning("Database not ready yet (attempt %s/%s)", attempt, max_retries)
            time.sleep(delay_seconds)


def run_grouping_job() -> None:
    db = SessionLocal()
    try:
        run_grouping_cycle(db)
    except Exception:
        logger.exception("Grouping job failed")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    wait_for_database()
    Base.metadata.create_all(bind=engine)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_grouping_job,
        "interval",
        seconds=settings.grouping_interval_seconds,
        id="grouping-job",
        replace_existing=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
