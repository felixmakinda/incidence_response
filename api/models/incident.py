from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class IncomingEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_address: str
    from_company: str
    subject: str
    body: str
    received_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class TriggerIncidentRequest(BaseModel):
    email_id: Optional[str] = None
    severity: Literal["P0", "P1", "P2"] = "P0"
    # Full email payload — used when email_id is a real IMAP ID not in mock data
    from_address: Optional[str] = None
    from_company: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class ToolCallRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    display_name: str
    params: dict = Field(default_factory=dict)
    result: Optional[dict] = None
    status: Literal["pending", "running", "success", "failed"] = "pending"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    depends_on: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class AgentThought(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    type: Literal["reasoning", "decision", "observation"] = "reasoning"


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str
    label: str
    description: str
    tool_name: str
    status: str = "info"


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: IncomingEmail
    severity: Literal["P0", "P1", "P2"] = "P0"
    status: Literal["idle", "running", "complete", "failed"] = "idle"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    thoughts: list[AgentThought] = Field(default_factory=list)
    timeline: list[TimelineEvent] = Field(default_factory=list)
