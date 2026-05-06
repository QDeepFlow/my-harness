from pathlib import Path

from internal.schema.message import ToolCall, ToolDefinition, ToolResult
from internal.tools.bsae_tool import BaseTool


class WriteFileTool(BaseTool):



    def __init__(self, work_dir: str):
        # 初始化工作区约束，转换为绝对路径方便后续安全校验
        self.work_dir = Path(work_dir).resolve()


    def tool_definiton(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_file",
            description="创建或覆盖写入一个文件。如果目录不存在会自动创建。请提供相对于工作区的相对路径。",
            input_schema= {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "要写入的文件路径，比如cmd/claw/main.py的路径信息"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入文件的内容字符串"
                    }
                },
                "required": ["path", "content"]
            }
        )


    def execute(self, tool_call: ToolCall) -> ToolResult:
        # 提取参数
        raw_path = tool_call.arguments.get("path", "").strip()
        content = tool_call.arguments.get("content", "")
        if not raw_path:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="缺少必填参数 path",
                is_error=True,
            )
        if not content:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="缺少必填参数 content",
                is_error=True,
            )

        # 安全防线：限制在工作区下操作，防止路径穿越
        target_path = (self.work_dir / raw_path).resolve()
        try:
            target_path.relative_to(self.work_dir)
        except ValueError:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="不允许访问工作区之外的路径",
                is_error=True,
            )

        # 自动创建缺失的父级目录
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件内容
        try:
            target_path.write_text(content, encoding="utf-8")
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"写入文件失败: {str(e)}",
                is_error=True,
            )

        return ToolResult(
            tool_call_id=tool_call.id,
            output=f"成功将内容写入到文件: {raw_path}",
            is_error=False,
        )
