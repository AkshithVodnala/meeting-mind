import json
import re
from datetime import datetime
from sqlmodel import Session
from huggingface_hub import InferenceClient
from app.config import settings
from app.models import MeetingJob, MeetingResult


# ── LLM Client ────────────────────────────────────────────────
client = InferenceClient(
    model=settings.model_id,
    token=settings.hf_token
)


def call_llm(system_prompt: str, user_content: str) -> str:
    """
    Send a prompt to HuggingFace LLM and return response text.
    """
    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return "[]"


def parse_json(response: str) -> list:
    """
    Safely parse LLM JSON response into a list.
    Handles cases where LLM adds extra text around JSON.
    """
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    print(f"Could not parse JSON: {response[:200]}")
    return []


def update_status(session: Session, job: MeetingJob, status: str):
    """Update job status in database."""
    job.status = status
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)


# ── Agent Steps ────────────────────────────────────────────────

def step_extract_actions(transcript: str) -> list:
    """
    Step 1: Extract action items from transcript.
    """
    system = """
You are an expert meeting analyst.
Extract all action items from the meeting transcript.
Return a JSON array only. No explanation outside JSON.
Each item must have exactly these fields:
[
  {
    "action": "clear description of what needs to be done",
    "priority": "High or Medium or Low"
  }
]
If no action items found return: []
Return ONLY the JSON array, nothing else.
"""
    response = call_llm(system, f"Extract action items from this transcript:\n\n{transcript}")
    return parse_json(response)


def step_assign_owners(transcript: str, action_items: list) -> list:
    """
    Step 2: Assign owners to each action item.
    """
    system = """
You are an expert meeting analyst.
You will be given a transcript and a list of action items.
For each action item identify who is responsible based on the transcript.
Return a JSON array only. No explanation outside JSON.
Each item must have exactly these fields:
[
  {
    "action": "the action item",
    "owner": "person's name or Unknown if not clear",
    "priority": "High or Medium or Low"
  }
]
Return ONLY the JSON array, nothing else.
"""
    content = f"""
Transcript:
{transcript}

Action items:
{json.dumps(action_items)}

Assign an owner to each action item based on who was mentioned in the transcript.
"""
    response = call_llm(system, content)
    return parse_json(response)


def step_detect_deadlines(transcript: str, action_items: list) -> list:
    """
    Step 3: Detect deadlines for each action item.
    """
    system = """
You are an expert meeting analyst.
You will be given a transcript and action items with owners.
For each action item detect the deadline from the transcript.
Look for phrases like: by Friday, end of week, next sprint, tomorrow, by EOD.
Return a JSON array only. No explanation outside JSON.
Each item must have exactly these fields:
[
  {
    "action": "the action item",
    "owner": "person's name",
    "priority": "High or Medium or Low",
    "deadline": "specific deadline or No deadline mentioned"
  }
]
Return ONLY the JSON array, nothing else.
"""
    content = f"""
Transcript:
{transcript}

Action items with owners:
{json.dumps(action_items)}

Detect deadlines for each action item.
"""
    response = call_llm(system, content)
    return parse_json(response)


def step_detect_risks(transcript: str) -> list:
    """
    Step 4: Detect risks and blockers from transcript.
    """
    system = """
You are an expert meeting analyst.
Extract all risks, blockers, concerns, or dependencies mentioned in the transcript.
Return a JSON array only. No explanation outside JSON.
Each item must have exactly these fields:
[
  {
    "risk": "clear description of the risk or blocker",
    "severity": "High or Medium or Low",
    "mentioned_by": "person who raised it or Unknown"
  }
]
If no risks found return: []
Return ONLY the JSON array, nothing else.
"""
    response = call_llm(system, f"Extract risks and blockers from this transcript:\n\n{transcript}")
    return parse_json(response)


def step_summarize(transcript: str, action_items: list, risks: list) -> tuple[str, int]:
    """
    Step 5: Generate summary and productivity score.
    """
    system = """
You are an expert meeting analyst.
Write a 3-4 sentence professional summary of the meeting.
Then give a productivity score from 0 to 100 based on:
- Were clear decisions made?
- Were owners assigned?
- Were deadlines set?
- Were risks identified?

Return your response in this exact format:
SUMMARY: your 3-4 sentence summary here
SCORE: number between 0 and 100
"""
    content = f"""
Transcript:
{transcript}

Action items found: {len(action_items)}
Risks found: {len(risks)}

Write a summary and productivity score.
"""
    response = call_llm(system, content)

    # Parse summary and score
    summary = ""
    score = 50

    try:
        if "SUMMARY:" in response:
            summary_part = response.split("SUMMARY:")[1]
            if "SCORE:" in summary_part:
                summary = summary_part.split("SCORE:")[0].strip()
                score_str = summary_part.split("SCORE:")[1].strip()
                score = int(re.search(r'\d+', score_str).group())
            else:
                summary = summary_part.strip()
    except Exception:
        summary = response
        score = 50

    score = max(0, min(100, score))
    return summary, score


# ── Main Orchestrator ──────────────────────────────────────────

def run_analysis(job_id: str, transcript: str, session: Session):
    """
    Main agent — runs all 5 steps in sequence.
    """
    job = session.get(MeetingJob, job_id)
    if not job:
        print(f"Job {job_id} not found")
        return

    try:
        # Step 1: Extract action items
        print(f"[Agent] Step 1: Extracting action items...")
        update_status(session, job, "extracting_actions")
        action_items = step_extract_actions(transcript)
        print(f"[Agent] Found {len(action_items)} action items")

        # Step 2: Assign owners
        print(f"[Agent] Step 2: Assigning owners...")
        update_status(session, job, "assigning_owners")
        action_items = step_assign_owners(transcript, action_items)

        # Step 3: Detect deadlines
        print(f"[Agent] Step 3: Detecting deadlines...")
        update_status(session, job, "detecting_deadlines")
        action_items = step_detect_deadlines(transcript, action_items)

        # Step 4: Detect risks
        print(f"[Agent] Step 4: Detecting risks...")
        update_status(session, job, "detecting_risks")
        risks = step_detect_risks(transcript)
        print(f"[Agent] Found {len(risks)} risks")

        # Step 5: Summarize
        print(f"[Agent] Step 5: Generating summary...")
        update_status(session, job, "summarizing")
        summary, score = step_summarize(transcript, action_items, risks)

        # Save result
        result = MeetingResult(
            job_id=job_id,
            action_items=json.dumps(action_items),
            owners=json.dumps([i.get("owner", "Unknown") for i in action_items]),
            deadlines=json.dumps([i.get("deadline", "None") for i in action_items]),
            risks=json.dumps(risks),
            summary=summary,
            productivity_score=score
        )
        session.add(result)
        update_status(session, job, "complete")
        session.commit()

        print(f"[Agent] Complete. Score: {score}/100")

    except Exception as e:
        print(f"[Agent] Error: {e}")
        job.error_message = str(e)
        update_status(session, job, "failed")
        session.commit()