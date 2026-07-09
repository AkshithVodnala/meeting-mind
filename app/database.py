from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

engine = create_engine(
    settings.database_url,
    echo=True if settings.app_env == "development" else False,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session