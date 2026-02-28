#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph工具调用Agent示例
功能：接收用户需求，自主识别所需工具类型，自动调用对应工具完成任务
支持工具：计算器、天气查询、文件读写
执行链路：用户输入需求 → 感知模块解析需求 → 规划模块匹配对应工具 → 行动模块调用工具执行 → 结果整合返回用户
"""

from typing import TypedDict, Sequence, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
import json
from dotenv import load_dotenv

# 导入系统提供的工具
from __tools__ import get_weather, write_file as system_write_file, read_file as system_read_file

load_dotenv()

# 初始化大模型
llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0).bind_tools([get_weather, system_write_file, system_read_file])

# ------------------------------
# 1. 定义自定义工具（计算器工具）
# ------------------------------
@tool
def calculator(expression: str) -> float:
    """
    计算器工具：计算数学表达式的结果，支持加减乘除、括号运算
    参数：
        expression: 字符串格式的数学表达式，例如"(10 + 5) * 3"
    返回：
        计算结果的浮点数
    """
    return eval(expression)

# 注册所有可用工具
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "calculator": calculator,
    "write_file": system_write_file,
    "read_file": system_read_file
}

# ------------------------------
# 2. 定义Agent状态（记忆模块）
# ------------------------------
class ToolCallState(TypedDict):
    # 对话上下文消息列表（短期记忆）
    messages: Sequence[BaseMessage]
    # 工具调用参数
    tool_call_args: dict[str, Any]
    # 选中的工具名称
    selected_tool: str
    # 工具执行返回的结果
    tool_result: Any

# ------------------------------
# 3. 规划节点（规划模块：识别需求匹配工具）
# ------------------------------
def tool_selection_node(state: ToolCallState) -> ToolCallState:
    """
    工具选择节点功能：分析用户需求，选择最合适的工具，并生成工具调用参数
    """
    user_request = state["messages"][-1].content
    
    system_prompt = SystemMessage(content=f"""
    你是工具选择助手，根据用户需求，从以下可用工具中选择最适合的一个：
    可用工具列表：{list(AVAILABLE_TOOLS.keys())}
    工具功能说明：
    1. get_weather: 查询指定城市的当前天气，参数为location（城市名）
    2. calculator: 计算数学表达式结果，参数为expression（数学表达式字符串）
    3. write_file: 写入内容到文件，参数为file_path（文件路径）、content（写入内容）
    4. read_file: 读取指定文件内容，参数为file_path（文件路径）
    请返回JSON格式结果，包含选中的工具名和调用参数：
    {{"tool_name": "工具名称", "tool_args": {{参数名: 参数值}}}}
    用户需求：{user_request}
    """)
    
    response = llm.invoke([system_prompt])
    selection = json.loads(response.content)
    
    return {
        **state,
        "selected_tool": selection["tool_name"],
        "tool_call_args": selection["tool_args"]
    }

# ------------------------------
# 4. 工具执行节点（行动模块：调用工具执行任务）
# ------------------------------
def tool_execution_node(state: ToolCallState) -> ToolCallState:
    """
    工具执行节点功能：根据规划节点的选择，调用对应工具，获取执行结果
    """
    tool = AVAILABLE_TOOLS[state["selected_tool"]]
    # 调用工具
    result = tool.invoke(state["tool_call_args"])
    
    return {
        **state,
        "tool_result": result,
        "messages": state["messages"] + [AIMessage(content=f"已调用{state['selected_tool']}工具，执行结果：{str(result)[:100]}...")]
    }

# ------------------------------
# 5. 结果生成节点（行动模块：整合结果返回用户）
# ------------------------------
def result_generation_node(state: ToolCallState) -> ToolCallState:
    """
    结果生成节点功能：将工具执行结果整理为自然语言回答返回给用户
    """
    user_request = state["messages"][-1].content
    tool_result = state["tool_result"]
    tool_name = state["selected_tool"]
    
    response = llm.invoke([
        SystemMessage(content=f"基于{tool_name}工具的执行结果，回答用户的问题，结果要简洁清晰。\n执行结果：{tool_result}"),
        HumanMessage(content=user_request)
    ])
    
    return {
        **state,
        "messages": state["messages"] + [response]
    }

# ------------------------------
# 6. 构建工具调用Agent
# ------------------------------
def build_tool_call_agent():
    workflow = StateGraph(ToolCallState)
    
    # 添加节点
    workflow.add_node("select_tool", tool_selection_node)
    workflow.add_node("execute_tool", tool_execution_node)
    workflow.add_node("generate_result", result_generation_node)
    
    # 设置执行流程
    workflow.set_entry_point("select_tool")
    workflow.add_edge("select_tool", "execute_tool")
    workflow.add_edge("execute_tool", "generate_result")
    workflow.add_edge("generate_result", END)
    
    return workflow.compile()

# ------------------------------
# 测试运行示例
# ------------------------------
if __name__ == "__main__":
    agent = build_tool_call_agent()
    
    # 测试用例1：天气查询
    test_query = "帮我查一下北京现在的天气怎么样"
    # 测试用例2：计算器
    # test_query = "计算1234乘以5678的结果是多少"
    # 测试用例3：文件操作
    # test_query = "帮我读取当前目录下test.txt文件的内容"
    
    initial_state = {
        "messages": [HumanMessage(content=test_query)],
        "tool_call_args": {},
        "selected_tool": "",
        "tool_result": None
    }
    
    result = agent.invoke(initial_state)
    
    print("用户需求：", test_query)
    print("最终回答：", result["messages"][-1].content)
    print("\n完整执行链路：用户输入需求 → 工具选择节点匹配get_weather工具 → 工具执行节点调用天气查询接口 → 结果生成节点整理回答返回")
