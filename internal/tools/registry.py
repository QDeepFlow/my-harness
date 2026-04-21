from abc import ABC, abstractmethod
from typing import List
from internal.schema.message import ToolDefinition, ToolCall, ToolResult


class ToolRegistry(ABC):
    """
    Registry 定义了工具的注册与分发执行接口。
    在 Python 中，通过抽象基类 (ABC) 来定义接口规范。
    """

    @abstractmethod
    def get_available_tools(self) -> List[ToolDefinition]:
        """
        返回当前系统挂载的所有可用工具的 Schema。
        供大模型在 System Prompt 或 Tools 字段中感知能力范围。
        """
        pass

    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        实际执行模型请求的工具，并返回结果。

        注：Python 的协程通常通过 async def 实现，
        如果你的工具涉及网络请求或 I/O，建议使用异步版本。
        """
        pass