from internal.schema.message import ToolDefinition, ToolResult
from internal.tools.bsae_tool import BaseTool


class BashTool(BaseTool):
    def __init__(self):
        pass

    def tool_definiton(self) -> ToolDefinition:
        return ToolDefinition()


    def execute(self, tool_call: str) -> ToolResult:
        return ToolResult()