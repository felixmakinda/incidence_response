import asyncio
from collections import defaultdict
from typing import AsyncGenerator
import json


class EventBus:
    """
    Fan-out pub/sub using asyncio.Queue.
    Multiple SSE connections for the same incident_id each get their own queue.
    Supports event replay on reconnect via history buffer.
    """

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._history: dict[str, list[dict]] = defaultdict(list)

    def subscribe(self, incident_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[incident_id].append(q)
        # Replay history for reconnecting clients
        for event in self._history[incident_id]:
            q.put_nowait(event)
        return q

    def unsubscribe(self, incident_id: str, queue: asyncio.Queue):
        try:
            self._subscribers[incident_id].remove(queue)
        except ValueError:
            pass

    async def publish(self, incident_id: str, event: dict):
        self._history[incident_id].append(event)
        for q in list(self._subscribers[incident_id]):
            await q.put(event)

    async def stream(self, incident_id: str) -> AsyncGenerator[str, None]:
        q = self.subscribe(incident_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    if event is None:  # sentinel to close stream
                        break
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(incident_id, q)

    def close_stream(self, incident_id: str):
        """Send sentinel to all subscribers to close their streams."""
        for q in list(self._subscribers[incident_id]):
            q.put_nowait(None)


event_bus = EventBus()
