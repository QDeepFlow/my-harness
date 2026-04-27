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
import os
from ast import arguments
from typing import List, Dict, Any

from openai import api_key, OpenAI

from internal.schema.message import Message, Role


class OpenAIProvider:

    def __init__(self, model: str):
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE_URL")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: List[Dict[str, Any]], available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        open_ai_msg = []
        for message in messages:
            print(f"Message: role={message['role']}, content={message.get('content', '')}")
            role = message['role']
            content = message['content']
            if role == "system":
                open_ai_msg.append({"role": "system", "content": content})

            # 如果role的角色是user,
            elif role == "user":
                msg_param = {"role": "user", "content": content}
                if message.get("tool_call_id"):
                    msg_param["role"] = "tool_call"
                    msg_param["tool_call_id"] = message["tool_call_id"]
                open_ai_msg.append(msg_param)

            # 如果role的角色是assistant, 需要判断是否包含工具调用，如果包含工具调用，则需要将工具调用的信息也转换成OpenAI API能够理解的格式
            elif role == "assistant":
                ast_param = {"role": "assistant", "content": content}
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    ast_param["tool_calls"] = [
                        {
                            "id": tc["tool_call_id"],
                            "type": "function",
                            "function": {
                                "name": tc["tool_call_name"],
                                "arguments": tc["tool_call_arguments"],
                            }
                        } for tc in tool_calls
                    ]
                open_ai_msg.append(ast_param)

        open_ai_tools = []
        if available_tools:
            for tool_def in available_tools:
                open_ai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool_def["name"],
                        "description": tool_def["description"],
                        "parameters": tool_def["input_schema"]
                    }
                })
        kwargs = {
            "model": self.model,
            "messages": open_ai_msg,
        }
        if open_ai_tools:
            kwargs["tools"] = open_ai_tools
        print(f"OpenAI API Request: {kwargs}")
        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            raise RuntimeError(f"OpenAI API Error: {e}")
        print(f"OpenAI API Response: {response}")
        if not response.choices:
            raise RuntimeError(f"OpenAI API Error: {response}")

        # 把open ai的返回结果转换成schema的格式返回回去
        response_content = response.choices[0].message
        result_msg = {
            "role": Role.ASSISTANT,
            "content": response_content,
            "tool_calls": []
        }
        if response_content.tool_calls:
            for msg_tool in response_content.tool_calls:
                if msg_tool["type"] == "function":
                    result_msg["tool_calls"].append({
                        "id": msg_tool["tool_call_id"],
                        "name" : msg_tool["name"],
                        "arguments" : msg_tool["arguments"],
                    })
        # 最后返回给调用方的结果应该是一个符合我们Message schema格式的字典
        return result_msg


