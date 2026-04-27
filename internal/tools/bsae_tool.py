from abc import ABC, abstractmethod

from internal.schema.message import ToolDefinition, ToolResult, ToolCall


class BaseTool(ABC):

    @abstractmethod
    def tool_definiton(self) -> ToolDefinition:
        """
        定义工具的 Schema 信息，供大模型在 System Prompt 或 Tools 字段中感知能力范围。
        """
        raise NotImplementedError()

    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        raise NotImplementedError()
