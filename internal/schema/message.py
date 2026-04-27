from enum import Enum
from typing import List, Optional, Any, Union
from pydantic import BaseModel, Field

# --- 1. Role 定义 ---
class Role(str, Enum):
    """定义消息的角色，这是与大模型沟通的基石"""
    SYSTEM = "system"       # 系统提示词：确立 Agent 的性格与红线
    USER = "user"           # 用户输入
    ASSISTANT = "assistant" # 模型的输出：包含推理(Reasoning)或工具调用(ToolCall)
    TOOL = "tool"           # 工具执行的返回结果 (Observation)

# --- 2. ToolCall 定义 ---
class ToolCall(BaseModel):
    """代表模型请求调用某个具体的工具"""
    id: str                 # 工具调用的唯一 ID
    name: str               # 想要调用的工具名称 (例如 "bash")
    # 在 Python 中，我们直接使用 dict 或 Any 来模拟 json.RawMessage 的延迟解析效果
    arguments: Union[str, dict, Any] 

# --- 3. Message 定义 ---
class Message(BaseModel):
    """代表上下文中传递的单条消息"""
    role: Role
    content: Optional[str] = None # 存放纯文本内容
    
    # 如果模型决定调用工具，此字段将被填充 (支持并行调用多个工具)
    # omitempty 在 Pydantic 中通过 default=None 和 exclude_none=True 实现
    tool_calls: Optional[List[ToolCall]] = Field(default=None, alias="tool_calls")
    
    # 如果这是对某个工具调用的响应，此字段必须填写
    tool_call_id: Optional[str] = Field(default=None, alias="tool_call_id")

# --- 4. ToolResult 定义 ---
class ToolResult(BaseModel):
    """代表工具在本地执行完毕后返回的物理结果"""
    tool_call_id: str
    output: str             # 工具执行的控制台输出或报错堆栈
    is_error: bool          # 标记是否失败，供后续的驾驭工程进行错误自愈

# --- 5. ToolDefinition 定义 ---
class ToolDefinition(BaseModel):
    """描述了一个大模型可以调用的工具元信息"""
    name: str
    description: str
    input_schema: dict      # 对应 JSON Schema
