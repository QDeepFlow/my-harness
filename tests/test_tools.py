import tempfile
import unittest
from pathlib import Path

from internal.schema.message import ToolCall
from internal.tools.InMemoryRegistry import InMemoryRegistry
from internal.tools.get_weather import GetWeatherTool
from internal.tools.read_file import ReadFileTool
from internal.tools.write_file import WriteFileTool


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

    def test_read_file_tool_truncates_long_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "big.txt"
            lines = [f"line-{i}" for i in range(2500)]
            file_path.write_text("\n".join(lines), encoding="utf-8")
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(id="call-t1", name="read_file", arguments={"path": "big.txt"})
            )

            self.assertFalse(result.is_error)
            self.assertIn("[截断]", result.output)
            self.assertIn("2000/2500", result.output)
            self.assertNotIn("line-2499", result.output)

    def test_read_file_tool_offset_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "lines.txt"
            file_path.write_text("a\nb\nc\nd\ne", encoding="utf-8")
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(
                    id="call-t2",
                    name="read_file",
                    arguments={"path": "lines.txt", "offset": 1, "limit": 2},
                )
            )

            self.assertFalse(result.is_error)
            self.assertEqual(result.output, "b\nc")

    def test_read_file_tool_offset_out_of_range(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            file_path = root / "short.txt"
            file_path.write_text("only line", encoding="utf-8")
            tool = ReadFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(
                    id="call-t3",
                    name="read_file",
                    arguments={"path": "short.txt", "offset": 5},
                )
            )

            self.assertTrue(result.is_error)
            self.assertIn("超出", result.output)

    def test_write_file_tool_writes_text_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool = WriteFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(
                    id="call-6",
                    name="write_file",
                    arguments={"path": "hello.txt", "content": "hello world"},
                )
            )

            self.assertFalse(result.is_error)
            self.assertIn("hello.txt", result.output)
            written = (Path(tmp_dir) / "hello.txt").read_text(encoding="utf-8")
            self.assertEqual(written, "hello world")

    def test_write_file_tool_blocks_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool = WriteFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(
                    id="call-7",
                    name="write_file",
                    arguments={
                        "path": "../secret.txt",
                        "content": "should not write",
                    },
                )
            )

            self.assertTrue(result.is_error)
            self.assertIn("工作区之外", result.output)

    def test_write_file_tool_auto_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tool = WriteFileTool(tmp_dir)

            result = tool.execute(
                ToolCall(
                    id="call-8",
                    name="write_file",
                    arguments={
                        "path": "deep/nested/dir/file.txt",
                        "content": "nested content",
                    },
                )
            )

            self.assertFalse(result.is_error)
            target = Path(tmp_dir) / "deep" / "nested" / "dir" / "file.txt"
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "nested content")

    def test_write_file_tool_missing_path(self) -> None:
        tool = WriteFileTool("/tmp")

        result = tool.execute(
            ToolCall(
                id="call-9",
                name="write_file",
                arguments={"content": "no path here"},
            )
        )

        self.assertTrue(result.is_error)
        self.assertIn("path", result.output)

    def test_write_file_tool_missing_content(self) -> None:
        tool = WriteFileTool("/tmp")

        result = tool.execute(
            ToolCall(
                id="call-10",
                name="write_file",
                arguments={"path": "foo.txt"},
            )
        )

        self.assertTrue(result.is_error)
        self.assertIn("content", result.output)


if __name__ == "__main__":
    unittest.main()
