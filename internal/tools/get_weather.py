from internal.schema.message import ToolDefinition, ToolResult, ToolCall
from internal.tools.bsae_tool import BaseTool


class GetWeatherTool(BaseTool):

    def tool_definiton(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_weather",
            description="Get weather data",
            input_schema= {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name"
                    },
                },
                "required": ["city"]
            }
        )


    def execute(self, tool_call: ToolCall) -> ToolResult:
        city_name = tool_call.arguments["city"]
        """
        没有调用真实的api，模拟返回天气数据
        """

        return ToolResult(
            tool_call_id=tool_call.id,
            output=f"模拟天气信息{city_name}的天气晴朗，温度25度， 北风",
            is_error=False
        )
