
import logging
import os

from internal.engine.loop import AgentEngine
from internal.logger import setup_logging
from internal.schema.message import Message, Role, ToolResult

setup_logging()


class MockLLMProvider:
    """模拟大模型的回复"""
    def __init__(self):
        self.counter = 0
    def generate(self, messages, tool_definitions):

        # 如果工具列表的值为空，那么开始的是第一阶段Phase1 Thinking阶段内容
        if not tool_definitions:
            return Message(
                role=Role.ASSISTANT,
                content="【推理中】目标是检查文件，我不能盲猜，我需要调用bash工具执行ls的命令"
            )

        self.counter += 1
        if self.counter == 1:
            return Message(
                role=Role.ASSISTANT,
                content="我需要调用 bash 工具来查看当前目录下的文件列表。",
                tool_calls=[{
                    "id": "call-1",
                    "name": "bash",
                    "arguments": {"command": "ls -la"}
                }]
            )
        return Message(
            role=Role.ASSISTANT,
            content="我看到内容啦，执行成功 "
        )
class MockToolRegistry:
    """模拟工具调用"""

    def get_available_tools(self):
        return ["bash", "ls", "-la"]

    def execute(self, tool_call):
        """直接返回一段伪造的终端输出"""
        return ToolResult(
            tool_call_id=tool_call.id,
            output="-rw-r--r--  1 user group  234 Oct 24 10:00 main.py\n",
            is_error=False
        )


def main():
    print("🚀Hello from my-harness!")
    
    # 1.首先是初始化大模型

    # 2， 初始化Tool Registry

    # 3. 初始化上下文管理器

    # 4.组装并启动核心的Engine
    agent_engine = AgentEngine(
        provider=MockLLMProvider(),
        registry=MockToolRegistry(),
        work_dir=os.getcwd(),
        enable_thinking=True
    )

    try:
        error_response = agent_engine.run("帮我检查下当前目录内容")
        if error_response:
            logging.error(f"引擎崩溃 {error_response}")
    except Exception as e:
        logging.error(f"引擎运行时发生异常: {str(e)}")

    logging.info("my-harness is up and running!")



if __name__ == "__main__":
    main()
