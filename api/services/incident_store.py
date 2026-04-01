from typing import Optional
from models.incident import Incident, ToolCallRecord


class IncidentStore:
    def __init__(self):
        self._incidents: dict[str, Incident] = {}

    def create(self, incident: Incident) -> Incident:
        self._incidents[incident.id] = incident
        return incident

    def get(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    def list_recent(self, limit: int = 20) -> list[Incident]:
        return sorted(
            self._incidents.values(),
            key=lambda i: i.started_at or "",
            reverse=True,
        )[:limit]

    def upsert_tool_call(self, incident_id: str, tool_call: ToolCallRecord):
        incident = self._incidents.get(incident_id)
        if not incident:
            return
        for i, tc in enumerate(incident.tool_calls):
            if tc.id == tool_call.id:
                incident.tool_calls[i] = tool_call
                return
        incident.tool_calls.append(tool_call)

    def update_status(self, incident_id: str, status: str, completed_at: Optional[str] = None):
        incident = self._incidents.get(incident_id)
        if incident:
            incident.status = status  # type: ignore
            if completed_at:
                incident.completed_at = completed_at


incident_store = IncidentStore()
