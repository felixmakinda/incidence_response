import json
import os
import time
import uuid
from datetime import datetime

from models.incident import AgentThought, Incident, TimelineEvent, ToolCallRecord
from openai import AsyncOpenAI
from services.event_bus import EventBus
from services.incident_store import incident_store
from tools.registry import tool_registry

from agent.function_definitions import TOOL_DEFINITIONS
from agent.prompt_builder import SYSTEM_PROMPT, build_incident_context

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def _now() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def _publish(event_bus: EventBus, incident_id: str, event_type: str, data: dict):
    await event_bus.publish(
        incident_id,
        {"event": event_type, "incident_id": incident_id, "timestamp": _now(), "data": data},
    )


async def run_incident_agent(incident: Incident, event_bus: EventBus):
    incident_id = incident.id

    # Mark as running
    incident.status = "running"
    incident.started_at = _now()
    incident_store.update_status(incident_id, "running")

    await _publish(event_bus, incident_id, "incident_started", {"email": incident.email.model_dump()})

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_incident_context(incident.email)},
    ]

    max_iterations = 12

    for _ in range(max_iterations):
        # Stream from OpenAI
        accumulated_content = ""
        accumulated_tool_calls: list[dict] = []
        thought_buffer = ""

        try:
            stream = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # Accumulate text content and emit thoughts
                if delta.content:
                    accumulated_content += delta.content
                    thought_buffer += delta.content
                    # Emit thought when we hit a sentence boundary or 120 chars
                    if any(c in thought_buffer for c in (".", "\n", "!")) or len(thought_buffer) > 120:
                        stripped = thought_buffer.strip()
                        if stripped:
                            thought = AgentThought(
                                id=str(uuid.uuid4()),
                                content=stripped,
                                timestamp=_now(),
                                type=_classify_thought(stripped),
                            )
                            incident.thoughts.append(thought)
                            await _publish(
                                event_bus,
                                incident_id,
                                "agent_thought",
                                {
                                    "thought_id": thought.id,
                                    "content": thought.content,
                                    "type": thought.type,
                                    "timestamp": thought.timestamp,
                                },
                            )
                        thought_buffer = ""

                # Accumulate tool calls from streaming deltas
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        while len(accumulated_tool_calls) <= idx:
                            accumulated_tool_calls.append(
                                {"id": "", "type": "function", "function": {"name": "", "arguments": ""}}
                            )
                        if tc_delta.id:
                            accumulated_tool_calls[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                accumulated_tool_calls[idx]["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                accumulated_tool_calls[idx]["function"]["arguments"] += tc_delta.function.arguments

            # Flush remaining thought buffer
            if thought_buffer.strip():
                thought = AgentThought(
                    id=str(uuid.uuid4()),
                    content=thought_buffer.strip(),
                    timestamp=_now(),
                    type=_classify_thought(thought_buffer),
                )
                incident.thoughts.append(thought)
                await _publish(
                    event_bus,
                    incident_id,
                    "agent_thought",
                    {"thought_id": thought.id, "content": thought.content, "type": thought.type, "timestamp": thought.timestamp},
                )

        except Exception as e:
            await _publish(event_bus, incident_id, "incident_failed", {"error": str(e)})
            incident_store.update_status(incident_id, "failed", _now())
            return

        # Append assistant message to history
        assistant_msg: dict = {"role": "assistant", "content": accumulated_content or None}
        if accumulated_tool_calls:
            assistant_msg["tool_calls"] = accumulated_tool_calls
        messages.append(assistant_msg)

        # No tool calls → agent is done
        if not accumulated_tool_calls:
            await _publish(event_bus, incident_id, "incident_complete", {"tool_count": len(incident.tool_calls)})
            incident_store.update_status(incident_id, "complete", _now())
            event_bus.close_stream(incident_id)
            return

        # Execute tool calls sequentially (preserves dependency ordering)
        for tc in accumulated_tool_calls:
            tool_call_id = tc["id"]
            tool_name = tc["function"]["name"]

            try:
                params = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                params = {}

            meta = tool_registry.get_meta(tool_name)
            record = ToolCallRecord(
                id=tool_call_id,
                tool_name=tool_name,
                display_name=meta["display_name"],
                params=params,
                status="running",
                started_at=_now(),
                depends_on=meta["depends_on"],
            )
            incident_store.upsert_tool_call(incident_id, record)

            await _publish(
                event_bus,
                incident_id,
                "tool_call_start",
                {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_name,
                    "display_name": meta["display_name"],
                    "icon": meta["icon"],
                    "params": params,
                    "depends_on": meta["depends_on"],
                },
            )

            t_start = time.monotonic()
            try:
                result = await tool_registry.execute(tool_name, params)
                duration_ms = int((time.monotonic() - t_start) * 1000)

                record.result = result
                record.status = "success"
                record.completed_at = _now()
                record.duration_ms = duration_ms
                incident_store.upsert_tool_call(incident_id, record)

                await _publish(
                    event_bus,
                    incident_id,
                    "tool_call_complete",
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                        "result": result,
                        "duration_ms": duration_ms,
                    },
                )

                # Timeline event
                tl = TimelineEvent(
                    timestamp=_now(),
                    label=meta["display_name"],
                    description=f"{meta['display_name']} action completed successfully",
                    tool_name=tool_name,
                    status="success",
                )
                incident.timeline.append(tl)

                messages.append(
                    {"role": "tool", "tool_call_id": tool_call_id, "content": json.dumps(result)}
                )

            except Exception as e:
                duration_ms = int((time.monotonic() - t_start) * 1000)
                record.status = "failed"
                record.error = str(e)
                record.completed_at = _now()
                record.duration_ms = duration_ms
                incident_store.upsert_tool_call(incident_id, record)

                await _publish(
                    event_bus,
                    incident_id,
                    "tool_call_failed",
                    {"tool_call_id": tool_call_id, "tool_name": tool_name, "error": str(e)},
                )
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call_id, "content": f"Error: {str(e)}"}
                )

    # Safety exit after max iterations
    await _publish(event_bus, incident_id, "incident_complete", {"tool_count": len(incident.tool_calls)})
    incident_store.update_status(incident_id, "complete", _now())
    event_bus.close_stream(incident_id)


def _classify_thought(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ("must", "should", "need to", "will", "going to", "first", "next", "then")):
        return "decision"
    if any(w in text_lower for w in ("noticed", "see", "result", "returned", "received", "completed", "done")):
        return "observation"
    return "reasoning"
