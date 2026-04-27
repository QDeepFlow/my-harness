from typing import List, Optional

from internal.provider.base import LLMProvider
from internal.schema.message import Message, Role, ToolCall, ToolDefinition


class MockProvider(LLMProvider):
    def __init__(self) -> None:
        self._tool_called = False

    def generate(
        self,
        messages: List[Message],
        available_tools: Optional[List[ToolDefinition]],
        scratchpad: Optional[List[str]] = None,
    ) -> Message:
        if available_tools is None:
            return Message(
                role=Role.ASSISTANT,
                content="我需要先查询天气工具，再根据工具结果组织最终答复。",
            )

        if not self._tool_called:
            self._tool_called = True
            return Message(
                role=Role.ASSISTANT,
                content="我来查询北京的天气。",
                tool_calls=[
                    ToolCall(
                        id="mock-call-1",
                        name="get_weather",
                        arguments={"city": "北京"},
                    )
                ],
            )

        tool_messages = [message for message in messages if message.role == Role.TOOL]
        latest_tool_output = tool_messages[-1].content if tool_messages else "未获取到天气数据。"
        return Message(
            role=Role.ASSISTANT,
            content=f"根据工具结果：{latest_tool_output}",
        )
