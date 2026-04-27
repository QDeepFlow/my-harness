import logging
from typing import List, Optional

from internal.provider.base import LLMProvider
from internal.schema.message import Message, Role

# 假设之前的代码分别保存在对应的模块中
# from provider import LLMProvider
# from schema import Message, Role, ToolCall
# from tools import Registry

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Engine")


class AgentEngine:
    """AgentEngine 是微型 OS 的核心驱动"""

    def __init__(self, provider: LLMProvider, registry, work_dir: str, enable_thinking: bool):
        self.provider = provider
        self.registry = registry
        # WorkDir (工作区): Agent 必须有一个明确的物理边界
        self.work_dir = work_dir

        # 引入thinking开关
        self.enable_thinking = enable_thinking

    def run(self, user_prompt: str) -> Optional[Exception]:
        """启动 Agent 的生命周期"""
        logger.info(f"[Engine] 引擎启动，锁定工作区: {self.work_dir}")

        # 1. 初始化会话的 Context (上下文内存)
        context_history: List[Message] = [
            Message(role=Role.SYSTEM, content="You are python-tiny-claw, an expert coding assistant. You have full access to tools in the workspace."),
            Message(role=Role.USER, content=user_prompt),
        ]
        reasoning_history: List[str] = []

        turn_count = 0

        # 2. The Main Loop: 心跳开始 (标准的 ReAct 循环)
        while True:
            turn_count += 1
            logger.info(f"========== [Turn {turn_count}] 开始 ==========")

            # 获取当前挂载的所有工具定义
            available_tools = self.registry.get_available_tools()

            # 向大模型发起推理请求 (包含 Reasoning)
            logger.info("[Engine] 正在思考 (Reasoning)...")

            # 如果启用了思考阶段，先让模型进行一次纯文本的推理，看看它的想法是什么
            if self.enable_thinking:
                response = self.provider.generate(context_history, None, reasoning_history)
                if response:
                    print(f"💭 思考中: {response.content}")
                    if response.content:
                        reasoning_history.append(response.content)

                else:
                    logger.error("思考阶段发生错误，无法继续执行。")
                    return Exception("思考阶段发生错误，无法继续执行。")
            # 开启阶段2行动
            try:
                # 在 Python 中，ctx (context) 通常不作为强制首参，除非是异步协程
                response_msg = self.provider.generate(context_history, available_tools, reasoning_history)
            except Exception as e:
                return Exception(f"模型生成失败: {str(e)}")

            # 将模型的响应完整追加到上下文历史中
            context_history.append(response_msg)

            # 如果模型回复了纯文本，打印出来
            if response_msg.content:
                print(f"🤖 模型: {response_msg.content}")

            # 3. 退出条件判断
            # 如果模型没有请求任何工具调用，说明它认为任务已经完成，跳出循环
            if not response_msg.tool_calls or len(response_msg.tool_calls) == 0:
                logger.info("[Engine] 任务完成，退出循环。")
                break

            # 4. 执行行动 (Action) 与 获取观察结果 (Observation)
            logger.info(f"[Engine] 模型请求调用 {len(response_msg.tool_calls)} 个工具...")

            for tool_call in response_msg.tool_calls:
                logger.info(f"  -> 🛠️ 执行工具: {tool_call.name}, 参数: {tool_call.arguments}")

                # 通过 Registry 路由并执行底层工具
                result = self.registry.execute(tool_call)

                if result.is_error:
                    logger.info(f"  -> ❌ 工具执行报错: {result.output}")
                else:
                    logger.info(f"  -> ✅ 工具执行成功 (返回 {len(result.output)} 字节)")

                # 将工具执行的观察结果 (Observation) 封装为 User Message 追加到上下文中
                # 注意：ToolCallID 必须携带！这是维系大模型推理链条的关键
                observation_msg = Message(
                    role=Role.TOOL,
                    content=result.output,
                    tool_call_id=tool_call.id,
                )
                context_history.append(observation_msg)

            # 循环回到开头，模型将带着新加入的 Observation 继续它的下一轮思考...

        return None
