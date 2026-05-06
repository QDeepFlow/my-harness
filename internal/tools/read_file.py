from pathlib import Path

from internal.schema.message import ToolCall, ToolDefinition, ToolResult
from internal.tools.bsae_tool import BaseTool


class ReadFileTool(BaseTool):
    """
    定义一个tool definition， 读取文件内容，输入参数为文件路径，输出参数为文件内容字符串。
    """
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir).resolve()

    def tool_definiton(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="读取指定路径的内容。如果路径是文件，则返回文件内容；如果路径是目录，则返回目录下的文件和子目录列表。路径应为相对工作区的路径。",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "读取文件路径，比如是cmd/claw/main.py的路径信息"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "起始行号（从0开始），默认0"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最多读取的行数，默认2000，超出自动截断"
                    },
                },
                "required": ["path"]
            }
        )


    def execute(self, tool_call: ToolCall) -> ToolResult:
        raw_path = tool_call.arguments.get("path", "").strip()
        if not raw_path:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="缺少必填参数 path",
                is_error=True,
            )

        target_path = (self.work_dir / raw_path).resolve()
        try:
            target_path.relative_to(self.work_dir)
        except ValueError:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="不允许访问工作区之外的路径",
                is_error=True,
            )

        if not target_path.exists():
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"路径不存在: {raw_path}",
                is_error=True,
            )

        if target_path.is_dir():
            entries = sorted(target_path.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
            lines = []
            for entry in entries:
                entry_type = "dir" if entry.is_dir() else "file"
                rel_path = entry.relative_to(self.work_dir)
                lines.append(f"[{entry_type}] {rel_path}")
            output = "\n".join(lines) if lines else f"目录为空: {raw_path}"
            return ToolResult(
                tool_call_id=tool_call.id,
                output=output,
                is_error=False,
            )

        try:
            content = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"文件不是 UTF-8 文本，无法直接读取: {raw_path}",
                is_error=True,
            )

        all_lines = content.splitlines()
        original_total = len(all_lines)
        max_lines = 2000

        offset = tool_call.arguments.get("offset", 0)
        raw_limit = tool_call.arguments.get("limit", max_lines)
        user_set_limit = "limit" in tool_call.arguments

        if offset >= original_total:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"offset {offset} 超出文件总行数 {original_total}",
                is_error=True,
            )

        all_lines = all_lines[offset:]
        remaining = len(all_lines)
        limit = min(raw_limit, max_lines)

        if limit < remaining:
            all_lines = all_lines[:limit]
            shown = limit
            truncated = not user_set_limit
        elif remaining > max_lines:
            all_lines = all_lines[:max_lines]
            shown = max_lines
            truncated = True
        else:
            shown = remaining
            truncated = False

        output = "\n".join(all_lines)
        if truncated:
            output += f"\n\n... [截断] 显示 {shown}/{original_total} 行，使用 offset/limit 参数读取其余部分。"

        return ToolResult(
            tool_call_id=tool_call.id,
            output=output,
            is_error=False,
        )
