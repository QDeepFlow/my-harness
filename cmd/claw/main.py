import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from internal.tools.InMemoryRegistry import InMemoryRegistry
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

def main():
    print("🚀Hello from my-harness!")

    provider_name = os.getenv("PROVIDER", "mock").lower()
    if provider_name == "openai":
        provider = OpenAIProvider(os.getenv("MODEL_NAME", "deepseek-chat"))
    else:
        provider = MockProvider()

    tool_registry = InMemoryRegistry(
        tools=[
            GetWeatherTool(),
            ReadFileTool(os.getcwd()),
            WriteFileTool(os.getcwd())
        ]
    )
    agent_engine = AgentEngine(
        provider=provider,
        registry=tool_registry,
        work_dir=os.getcwd(),
        enable_thinking=False
    )

    try:
        error_response = agent_engine.run("请在当前目录下创建一个hello.txt文件，内容是Hello, Tiny Claw!")
        if error_response:
            logging.error(f"引擎崩溃 {error_response}")
    except Exception as e:
        logging.error(f"引擎运行时发生异常: {str(e)}")

    logging.info("my-harness is up and running!")



if __name__ == "__main__":
    main()
