from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import create_db_and_tables
from app.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup — creates database tables.
    """
    create_db_and_tables()
    print("✅ Database ready")
    print("✅ Meeting Mind is running")
    yield
    print("Shutting down Meeting Mind")


app = FastAPI(
    title="Meeting Mind",
    description="AI agent that extracts action items from meeting transcripts",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)