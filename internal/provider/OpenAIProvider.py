# class MockLLMProvider:
#     """模拟大模型的回复"""
#     def __init__(self):
#         self.counter = 0
#     def generate(self, messages, tool_definitions):
#
#         # 如果工具列表的值为空，那么开始的是第一阶段Phase1 Thinking阶段内容
#         if not tool_definitions:
#             return Message(
#                 role=Role.ASSISTANT,
#                 content="【推理中】目标是检查文件，我不能盲猜，我需要调用bash工具执行ls的命令"
#             )
#
#         self.counter += 1
#         if self.counter == 1:
#             return Message(
#                 role=Role.ASSISTANT,
#                 content="我需要调用 bash 工具来查看当前目录下的文件列表。",
#                 tool_calls=[{
#                     "id": "call-1",
#                     "name": "bash",
#                     "arguments": {"command": "ls -la"}
#                 }]
#             )
#         return Message(
#             role=Role.ASSISTANT,
#             content="我看到内容啦，执行成功 "
#         )

"""
我们在上一步中操作了一个非常简单的 MockLLMProvider 来模拟大模型的回复，但在实际应用中，我们需要一个真正能够与 OpenAI API 进行交互的 Provider 来替换它。
我们采用是在schema中的定义的Message对象作为我们和大模型交互的统一标准，OpenAIProvider的核心职责就是将这个Message对象转换成OpenAI API能够理解的格式，并且将OpenAI API的回复转换回Message对象。
"""
import json
import os
from typing import Any, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from internal.schema.message import Message, Role, ToolCall, ToolDefinition

load_dotenv(override=True)


class OpenAIProvider:

    def __init__(self, model: str):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("BASE_URL")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _message_to_openai(self, message: Message) -> dict[str, Any]:
        if message.role == Role.SYSTEM:
            return {"role": "system", "content": message.content or ""}

        if message.role == Role.USER:
            return {"role": "user", "content": message.content or ""}

        if message.role == Role.TOOL:
            if not message.tool_call_id:
                raise ValueError("Tool message requires tool_call_id")
            return {
                "role": "tool",
                "tool_call_id": message.tool_call_id,
                "content": message.content or "",
            }

        assistant_msg: dict[str, Any] = {
            "role": "assistant",
            "content": message.content or "",
        }
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments
                        if isinstance(tool_call.arguments, str)
                        else json.dumps(tool_call.arguments, ensure_ascii=False),
                    },
                }
                for tool_call in message.tool_calls
            ]
        return assistant_msg

    def _tools_to_openai(self, available_tools: Optional[List[ToolDefinition]]) -> list[dict[str, Any]]:
        open_ai_tools: list[dict[str, Any]] = []
        if available_tools:
            for tool_def in available_tools:
                open_ai_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool_def.name,
                            "description": tool_def.description,
                            "parameters": tool_def.input_schema,
                        },
                    }
                )
        return open_ai_tools

    def _scratchpad_to_openai(self, scratchpad: Optional[List[str]]) -> Optional[dict[str, Any]]:
        if not scratchpad:
            return None

        content = "\n\n".join(
            f"[Reasoning note {index}] {note}"
            for index, note in enumerate(scratchpad, start=1)
            if note
        )
        if not content:
            return None

        return {
            "role": "system",
            "content": (
                "Internal reasoning scratchpad. These notes are for planning only. "
                "They are not final answers and should not be treated as already-sent assistant messages.\n\n"
                f"{content}"
            ),
        }

    def generate(
        self,
        messages: List[Message],
        available_tools: Optional[List[ToolDefinition]],
        scratchpad: Optional[List[str]] = None,
    ) -> Message:
        open_ai_msg = [self._message_to_openai(message) for message in messages]
        scratchpad_msg = self._scratchpad_to_openai(scratchpad)
        if scratchpad_msg:
            insert_index = 1 if open_ai_msg and open_ai_msg[0]["role"] == "system" else 0
            open_ai_msg.insert(insert_index, scratchpad_msg)
        kwargs = {
            "model": self.model,
            "messages": open_ai_msg,
        }
        open_ai_tools = self._tools_to_openai(available_tools)
        if open_ai_tools:
            kwargs["tools"] = open_ai_tools
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {e}")
        if not response.choices:
            raise RuntimeError(f"OpenAI API Error: {response}")

        response_message = response.choices[0].message

        print("===="*10)
        print(f"OpenAI API Response: {response_message}")
        print("===="*10)


        tool_calls: list[ToolCall] = []
        if response_message.tool_calls:
            for msg_tool in response_message.tool_calls:
                if msg_tool.type != "function":
                    continue
                raw_arguments = msg_tool.function.arguments
                try:
                    arguments: Any = json.loads(raw_arguments)
                except (TypeError, json.JSONDecodeError):
                    arguments = raw_arguments
                tool_calls.append(
                    ToolCall(
                        id=msg_tool.id,
                        name=msg_tool.function.name,
                        arguments=arguments,
                    )
                )

        return Message(
            role=Role.ASSISTANT,
            content=response_message.content,
            tool_calls=tool_calls or None,
        )
