import subprocess

from internal.schema.message import ToolCall, ToolDefinition, ToolResult
from internal.tools.bsae_tool import BaseTool


class BashTool(BaseTool):

    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    def tool_definiton(self) -> ToolDefinition:
        return ToolDefinition(
            name="bash",
            description="在当前工作区执行任意的 bash 命令。支持链式命令(如 &&)。返回标准输出(stdout)和标准错误(stderr)。",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "要执行的 bash 命令，例如: ls -la 或 go test ./...",
                    },
                },
                "required": ["command"],
            },
        )

    def execute(self, tool_call: ToolCall) -> ToolResult:
        command = tool_call.arguments.get("command", "").strip()
        if not command:
            return ToolResult(
                tool_call_id=tool_call.id,
                output="缺少必填参数 command",
                is_error=True,
            )

        try:
            result = subprocess.run(
                command,
                shell=True,            # 支持管道、&&、环境变量等 Shell 语法
                cwd=self.work_dir,     # 锁定在工作区下执行
                capture_output=True,
                timeout=30,            # 防止大模型运行 top、tail -f 等卡死进程
            )
        except subprocess.TimeoutExpired as e:
            # 超时不返回 is_error，把已捕获的输出和警告一起给模型，让模型自行决策
            output = e.output.decode("utf-8", errors="replace") if e.output else ""
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            combined = output + stderr
            return ToolResult(
                tool_call_id=tool_call.id,
                output=combined + "\n[警告: 命令执行超时(30s)，已被系统强制终止。如果是启动常驻服务，请尝试将其转入后台。]",
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"命令执行异常: {e}",
                is_error=True,
            )

        output_str = result.stdout.decode("utf-8", errors="replace")
        stderr_str = result.stderr.decode("utf-8", errors="replace")

        if result.returncode != 0:
            # 命令失败也返回 is_error=False，把错误信息原样透传给模型自愈
            combined = output_str + stderr_str
            return ToolResult(
                tool_call_id=tool_call.id,
                output=f"命令执行失败 (exit code {result.returncode}):\n{combined}",
                is_error=False,
            )

        combined = output_str + stderr_str
        if not combined:
            # 命令成功但没有输出（如 mkdir、touch），给出明确反馈避免模型困惑
            return ToolResult(
                tool_call_id=tool_call.id,
                output="命令执行成功，无终端输出。",
                is_error=False,
            )

        max_len = 8000
        if len(combined) > max_len:
            # 防止大输出撑爆上下文窗口
            combined = combined[:max_len] + f"\n\n...[终端输出过长，已截断至前 {max_len} 字节]..."

        return ToolResult(
            tool_call_id=tool_call.id,
            output=combined,
            is_error=False,
        )
