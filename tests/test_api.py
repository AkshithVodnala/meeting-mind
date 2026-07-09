import pytest
from unittest.mock import patch
from app.models import MeetingJob


# ── Health Check ───────────────────────────────────────────────

def test_health_check(client):
    """Test health endpoint returns ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "meeting-mind"


# ── Home Page ──────────────────────────────────────────────────

def test_home_page_loads(client):
    """Test home page returns 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Meeting Mind" in response.text


# ── Analyze Endpoint ───────────────────────────────────────────

def test_analyze_returns_job_id(client):
    """Test that analyze endpoint returns a job ID."""
    with patch("app.routers.threading.Thread"):
        response = client.post("/analyze", json={
            "title": "Test Meeting",
            "transcript": "John: We need to update the login page by Friday. Sarah: I will handle it. Mike: I will fix the bug by Wednesday."
        })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert data["title"] == "Test Meeting"


def test_analyze_empty_transcript_returns_400(client):
    """Test that empty transcript returns 400 error."""
    response = client.post("/analyze", json={
        "title": "Test",
        "transcript": ""
    })
    assert response.status_code == 400


def test_analyze_short_transcript_returns_400(client):
    """Test that too short transcript returns 400 error."""
    response = client.post("/analyze", json={
        "title": "Test",
        "transcript": "Too short"
    })
    assert response.status_code == 400


def test_analyze_missing_transcript_returns_422(client):
    """Test that missing transcript field returns 422."""
    response = client.post("/analyze", json={
        "title": "Test Meeting"
    })
    assert response.status_code == 422


# ── Status Endpoint ────────────────────────────────────────────

def test_status_returns_pending(client):
    """Test that status endpoint returns pending for new job."""
    with patch("app.routers.threading.Thread"):
        response = client.post("/analyze", json={
            "title": "Test Meeting",
            "transcript": "John: We need to update the login page by Friday. Sarah: I will handle it. Mike: I will fix the bug by Wednesday."
        })
    job_id = response.json()["id"]
    status_response = client.get(f"/status/{job_id}")
    assert status_response.status_code == 200
    assert status_response.json()["id"] == job_id


def test_status_invalid_job_returns_404(client):
    """Test that invalid job ID returns 404."""
    response = client.get("/status/invalid-job-id-123")
    assert response.status_code == 404


# ── Result Page ────────────────────────────────────────────────

def test_result_page_loads(client):
    """Test result page loads for valid job."""
    with patch("app.routers.threading.Thread"):
        response = client.post("/analyze", json={
            "title": "Test Meeting",
            "transcript": "John: We need to update the login page by Friday. Sarah: I will handle it. Mike: I will fix the bug by Wednesday."
        })
    job_id = response.json()["id"]
    result_response = client.get(f"/result/{job_id}")
    assert result_response.status_code == 200


def test_result_page_invalid_job_returns_404(client):
    """Test result page returns 404 for invalid job."""
    response = client.get("/result/invalid-job-id-123")
    assert response.status_code == 404