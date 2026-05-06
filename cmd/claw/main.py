import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from internal.tools.InMemoryRegistry import InMemoryRegistry
from internal.tools.bash import BashTool
from internal.tools.get_weather import GetWeatherTool
from internal.tools.read_file import ReadFileTool
from internal.tools.write_file import WriteFileTool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from internal.engine.loop import AgentEngine
from internal.logger import setup_logging
from internal.provider.MockProvider import MockProvider
from internal.provider.OpenAIProvider import OpenAIProvider

setup_logging()
load_dotenv()

logger = logging.getLogger("Main")


def main():
    logger.info("my-harness 启动")

    provider_name = os.getenv("PROVIDER", "mock").lower()
    if provider_name == "openai":
        provider = OpenAIProvider(os.getenv("MODEL_NAME", "deepseek-chat"))
    else:
        provider = MockProvider()

    tool_registry = InMemoryRegistry(
        tools=[
            GetWeatherTool(),
            ReadFileTool(os.getcwd()),
            WriteFileTool(os.getcwd()),
            BashTool(os.getcwd()),
        ]
    )
    agent_engine = AgentEngine(
        provider=provider,
        registry=tool_registry,
        work_dir=os.getcwd(),
        enable_thinking=False,
    )

    try:
        error_response = agent_engine.run(
            user_prompt="接下来执行这几个步骤：1.使用bash命令查看下当前的python的版本 2. 然后创建一个hello world的python文件 3. 运行这个文件，保证没有问题"
        )
        if error_response:
            logger.error("引擎崩溃 %s", error_response)
    except Exception as e:
        logger.error("引擎运行时发生异常: %s", str(e))

    logger.info("my-harness 已退出")


if __name__ == "__main__":
    main()
