import os
import tempfile
import unittest

from internal.engine.loop import AgentEngine
from internal.provider.MockProvider import MockProvider
from internal.tools.InMemoryRegistry import InMemoryRegistry
from internal.tools.get_weather import GetWeatherTool
from internal.tools.read_file import ReadFileTool


class EngineTests(unittest.TestCase):
    def test_engine_completes_mock_provider_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            registry = InMemoryRegistry(
                [
                    GetWeatherTool(),
                    ReadFileTool(tmp_dir),
                ]
            )
            engine = AgentEngine(
                provider=MockProvider(),
                registry=registry,
                work_dir=os.getcwd(),
                enable_thinking=True,
            )

            result = engine.run("帮我看下北京的天气如何？")

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
