import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session


# ── Test Database ──────────────────────────────────────────────
# Uses in-memory SQLite so tests never touch your real database

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ── Sample Data ────────────────────────────────────────────────

@pytest.fixture
def sample_transcript():
    return """
    John: We need to update the login page by Friday.
    Sarah: I can handle the backend changes.
    Mike: I will fix the payment bug by Wednesday.
    Sarah: The third party API is unstable, that is a risk.
    John: Good point. Mike can you also write the tests by end of sprint?
    Mike: Sure I will handle that.
    """


@pytest.fixture
def sample_action_items():
    return [
        {"action": "Update login page", "priority": "High"},
        {"action": "Fix payment bug", "priority": "Medium"},
        {"action": "Write unit tests", "priority": "Low"}
    ]


@pytest.fixture
def sample_action_items_with_owners():
    return [
        {"action": "Update login page", "priority": "High", "owner": "Sarah"},
        {"action": "Fix payment bug", "priority": "Medium", "owner": "Mike"},
        {"action": "Write unit tests", "priority": "Low", "owner": "Mike"}
    ]