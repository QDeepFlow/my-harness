import logging
from typing import List, Optional

from internal.provider.base import LLMProvider
from internal.schema.message import Message, Role

logger = logging.getLogger("Engine")


class AgentEngine:
    """AgentEngine 是微型 OS 的核心驱动"""

    def __init__(self, provider: LLMProvider, registry, work_dir: str, enable_thinking: bool):
        self.provider = provider
        self.registry = registry
        self.work_dir = work_dir
        self.enable_thinking = enable_thinking

    def run(self, user_prompt: str) -> Optional[Exception]:
        """启动 Agent 的生命周期"""
        logger.info("引擎启动，锁定工作区: %s", self.work_dir)
        logger.info("慢思考模式 (Thinking Phase): %s", self.enable_thinking)

        # 初始化会话上下文
        context_history: List[Message] = [
            Message(role=Role.SYSTEM, content="You are python-tiny-claw, an expert coding assistant. You have full access to tools in the workspace."),
            Message(role=Role.USER, content=user_prompt),
        ]
        reasoning_history: List[str] = []

        turn_count = 0

        # The Main Loop: 标准的 ReAct 循环
        while True:
            turn_count += 1
            print(f"\n========== [Turn {turn_count}] 开始 ==========")

            # 获取当前挂载的所有工具定义
            available_tools = self.registry.get_available_tools()

            # 如果启用了思考阶段，先让模型进行一次纯文本推理
            if self.enable_thinking and turn_count == 1:
                response = self.provider.generate(context_history, None, reasoning_history)
                if response:
                    print(f"💭 思考中: {response.content}")
                    if response.content:
                        reasoning_history.append(response.content)
                else:
                    logger.error("思考阶段发生错误，无法继续执行。")
                    return Exception("思考阶段发生错误，无法继续执行。")

            # 行动阶段：挂载工具，等待模型采取行动
            logger.info("[Phase 2] 恢复工具挂载，等待模型采取行动...")

            try:
                response_msg = self.provider.generate(context_history, available_tools, reasoning_history)
            except Exception as e:
                return Exception(f"模型生成失败: {str(e)}")

            # 将模型响应追加到上下文历史
            context_history.append(response_msg)

            # 如果模型回复了纯文本，打印对外回复
            if response_msg.content:
                print(f"🤖 [对外回复]: \n{response_msg.content}")

            # 退出条件：模型没有请求任何工具调用，任务完成
            if not response_msg.tool_calls or len(response_msg.tool_calls) == 0:
                logger.info("模型未请求调用工具，任务宣告完成。")
                break

            # 执行行动 (Action) 与获取观察结果 (Observation)
            logger.info("模型请求调用 %d 个工具...", len(response_msg.tool_calls))

            for tool_call in response_msg.tool_calls:
                logger.info("  -> 🛠️ 执行工具: %s, 参数: %s", tool_call.name, tool_call.arguments)

                # 通过 Registry 路由并执行底层工具
                result = self.registry.execute(tool_call)

                if result.is_error:
                    logger.info("  -> ❌ 工具执行报错: %s", result.output)
                else:
                    logger.info("  -> ✅ 工具执行成功 (返回 %d 字节)", len(result.output))

                # 将工具执行的观察结果封装为 Tool Message 追加到上下文
                observation_msg = Message(
                    role=Role.TOOL,
                    content=result.output,
                    tool_call_id=tool_call.id,
                )
                context_history.append(observation_msg)

            # 循环回到开头，模型将带着新加入的 Observation 继续下一轮思考

        return None
