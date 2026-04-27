import tempfile
import unittest
from pathlib import Path

from internal.schema.message import ToolCall
from internal.tools.InMemoryRegistry import InMemoryRegistry
from internal.tools.get_weather import GetWeatherTool
from internal.tools.read_file import ReadFileTool


class ToolTests(unittest.TestCase):
    def test_registry_executes_weather_tool(self) -> None:
        registry = InMemoryRegistry([GetWeatherTool()])

        result = registry.execute(
            ToolCall(id="call-1", name="get_weather", arguments={"city": "北京"})
        )

        self.assertFalse(result.is_error)
        self.assertEqual(result.tool_call_id, "call-1")
        self.assertIn("北京", result.output)

    def test_registry_returns_error_for_unknown_tool(self) -> None:
        registry = InMemoryRegistry([GetWeatherTool()])

        result = registry.execute(
            ToolCall(id="call-2", name="missing_tool", arguments={})
        )

        self.assertTrue(result.is_error)
        self.assertEqual(result.tool_call_id, "call-2")
        self.assertIn("不存在", result.output)

    def test_read_file_tool_reads_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "note.txt"
            file_path.write_text("hello tool", encoding="utf-8")
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(id="call-3", name="read_file", arguments={"path": "note.txt"})
            )

            self.assertFalse(result.is_error)
            self.assertEqual(result.output, "hello tool")

    def test_read_file_tool_lists_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "subdir").mkdir()
            (root / "note.txt").write_text("hello tool", encoding="utf-8")
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(id="call-4", name="read_file", arguments={"path": "."})
            )

            self.assertFalse(result.is_error)
            self.assertIn("[dir] subdir", result.output)
            self.assertIn("[file] note.txt", result.output)

    def test_read_file_tool_blocks_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(id="call-5", name="read_file", arguments={"path": "../secret.txt"})
            )

            self.assertTrue(result.is_error)
            self.assertIn("工作区之外", result.output)


if __name__ == "__main__":
    unittest.main()
