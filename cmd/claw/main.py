
import logging
import os

from internal.engine.loop import AgentEngine
from internal.logger import setup_logging
from internal.provider.OpenAIProvider import OpenAIProvider
from internal.schema.message import Message, Role, ToolResult, ToolDefinition

setup_logging()


class MockToolRegistry:
    """模拟工具调用"""

    def get_available_tools(self) -> list[ToolDefinition]:
        return [{
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "要查询天气的城市名称"
                    }
                },
                "required": ["city"]
            }
        }]

    def execute(self, tool_call):
        logging.info("Mock tool called")
        return ToolResult(
            tool_call_id=tool_call.id,
            output=f"模拟天气信息: {tool_call.arguments.get('city', '未知城市')} 的天气晴朗，温度25°C",
            is_error=False
        )

def main():
    print("🚀Hello from my-harness!")
    
    # 1.首先是初始化大模型

    # 2， 初始化Tool Registry

    # 3. 初始化上下文管理器

    # 4.组装并启动核心的Engine
    agent_engine = AgentEngine(
        provider=OpenAIProvider("deepseek-chat"),
        registry=MockToolRegistry(),
        work_dir=os.getcwd(),
        enable_thinking=True
    )

    try:
        error_response = agent_engine.run("帮我看下北京的天气如何？")
        if error_response:
            logging.error(f"引擎崩溃 {error_response}")
    except Exception as e:
        logging.error(f"引擎运行时发生异常: {str(e)}")

    logging.info("my-harness is up and running!")



if __name__ == "__main__":
    main()
