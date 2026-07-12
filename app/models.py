from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid
import json


def generate_uuid() -> str:
    return str(uuid.uuid4())


class MeetingJob(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    title: str = Field(default="Untitled Meeting")
    transcript: str
    status: str = Field(default="pending")  # pending | running | complete | failed
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MeetingResult(SQLModel, table=True):
    id: str = Field(default_factory=generate_uuid, primary_key=True)
    job_id: str = Field(foreign_key="meetingjob.id")
    action_items: str = Field(default="[]")   # JSON string
    owners: str = Field(default="[]")         # JSON string
    deadlines: str = Field(default="[]")      # JSON string
    risks: str = Field(default="[]")          # JSON string
    summary: str = Field(default="")
    productivity_score: int = Field(default=0)  # 0-100
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def get_action_items(self) -> list:
        return json.loads(self.action_items)

    def get_owners(self) -> list:
        return json.loads(self.owners)

    def get_deadlines(self) -> list:
        return json.loads(self.deadlines)

    def get_risks(self) -> list:
        return json.loads(self.risks)


# API schemas
class MeetingRequest(SQLModel):
    title: str = "Untitled Meeting"
    transcript: str


class MeetingJobResponse(SQLModel):
    id: str
    title: str
    status: str
    created_at: datetime