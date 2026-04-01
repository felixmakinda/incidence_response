from abc import ABC, abstractmethod
from typing import Any
import asyncio
import random


class BaseTool(ABC):
    name: str
    display_name: str
    depends_on: list[str] = []

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        ...

    async def simulate_latency(self, min_ms: int = 300, max_ms: int = 1100):
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)
