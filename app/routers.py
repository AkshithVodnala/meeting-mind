import threading
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    MeetingJob,
    MeetingResult,
    MeetingRequest,
    MeetingJobResponse
)
from app.agent import run_analysis

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def run_agent_in_background(job_id: str, transcript: str):
    """
    Run agent in background thread so API responds immediately.
    """
    from app.database import engine
    from sqlmodel import Session
    with Session(engine) as session:
        run_analysis(job_id, transcript, session)


# ── Pages ──────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    session: Session = Depends(get_session)
):
    """Serve main dashboard page with past meetings list."""
    statement = select(MeetingJob).order_by(MeetingJob.created_at.desc())
    jobs = session.exec(statement).all()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "jobs": jobs}
    )


@router.get("/result/{job_id}", response_class=HTMLResponse)
def result_page(
    job_id: str,
    request: Request,
    session: Session = Depends(get_session)
):
    """Serve result page for a specific meeting analysis."""
    job = session.get(MeetingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = None
    if job.status == "complete":
        statement = select(MeetingResult).where(
            MeetingResult.job_id == job_id
        )
        result = session.exec(statement).first()

    return templates.TemplateResponse(
        "result.html",
        {"request": request, "job": job, "result": result}
    )


# ── API Endpoints ──────────────────────────────────────────────

@router.post("/analyze", response_model=MeetingJobResponse)
def analyze_meeting(
    body: MeetingRequest,
    session: Session = Depends(get_session)
):
    """
    Accept meeting transcript, create job,
    start agent in background, return job ID immediately.
    """
    if not body.transcript.strip():
        raise HTTPException(
            status_code=400,
            detail="Transcript cannot be empty"
        )

    if len(body.transcript.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Transcript too short. Please paste the full meeting transcript."
        )

    # Create job
    job = MeetingJob(
        title=body.title,
        transcript=body.transcript
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    # Start agent in background
    thread = threading.Thread(
        target=run_agent_in_background,
        args=(job.id, body.transcript),
        daemon=True
    )
    thread.start()

    return MeetingJobResponse(
        id=job.id,
        title=job.title,
        status=job.status,
        created_at=job.created_at
    )


@router.get("/status/{job_id}")
def get_status(
    job_id: str,
    session: Session = Depends(get_session)
):
    """
    Poll this endpoint to get current job status.
    Frontend polls every 3 seconds.
    """
    job = session.get(MeetingJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "status": job.status,
        "error_message": job.error_message
    }


@router.get("/health")
def health():
    """Health check for Docker and CI."""
    return {"status": "ok", "service": "meeting-mind"}