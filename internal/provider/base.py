from abc import ABC, abstractmethod
from typing import List, Optional

from internal.schema.message import Message, ToolDefinition


class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self,
        messages: List[Message],
        available_tools: Optional[List[ToolDefinition]],
        scratchpad: Optional[List[str]] = None,
    ) -> Message:
        """Generate the next assistant message from the current context."""
        raise NotImplementedError
