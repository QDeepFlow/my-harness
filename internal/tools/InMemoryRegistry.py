import logging
from typing import List, Dict

from internal.schema.message import ToolCall, ToolResult, ToolDefinition
from internal.tools.bsae_tool import BaseTool
from internal.tools.registry import ToolRegistry

logger = logging.getLogger("Registry")


class InMemoryRegistry(ToolRegistry):

    def __init__(self, tools: List[BaseTool]):
        self._tools: Dict[str, BaseTool] = {}
        for tool in tools:
            name = tool.tool_definiton().name
            self._tools[name] = tool
            logger.info("成功挂载工具: %s", name)

    def get_available_tools(self) -> List[ToolDefinition]:

        return [tool.tool_definiton() for tool in self._tools.values()]

    def execute(self, tool_call: ToolCall) -> ToolResult:
        tool = self._tools.get(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"工具 {tool_call.name} 不存在",
                is_error=True,
            )
        try:
            tool_result = tool.execute(tool_call)
            return ToolResult(
                tool_call_id=tool_call.id,
                output=tool_result.output,
                is_error=tool_result.is_error,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=str(e),
                is_error=True,
            )
