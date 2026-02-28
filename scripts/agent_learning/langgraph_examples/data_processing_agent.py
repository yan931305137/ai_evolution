#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph数据处理Agent示例
功能：接收用户上传的结构化数据，自主完成数据清洗、统计计算、分析输出全流程
执行链路：用户上传数据+需求 → 感知模块解析需求和数据格式 → 规划模块拆解处理步骤 → 行动模块依次执行清洗/计算/分析 → 整合结果返回
"""

from typing import TypedDict, Sequence, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import pandas as pd
import json
from dotenv import load_dotenv

load_dotenv()

# 初始化大模型
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# ------------------------------
# 1. 定义Agent状态（记忆模块）
# ------------------------------
class DataProcessState(TypedDict):
    # 对话上下文消息列表（短期记忆）
    messages: Sequence[BaseMessage]
    # 原始用户上传数据（DataFrame格式转成字典存储）
    raw_data: Dict[str, Any]
    # 清洗后的数据
    cleaned_data: Dict[str, Any]
    # 计算得到的统计结果
    stats_result: Dict[str, Any]
    # 规划得到的处理步骤列表
    process_steps: list[str]
    # 当前执行到的步骤索引
    current_step: int

# ------------------------------
# 2. 规划节点（规划模块：拆解数据处理步骤）
# ------------------------------
def plan_process_node(state: DataProcessState) -> DataProcessState:
    """
    规划节点功能：解析用户数据处理需求，拆解为可执行的步骤列表
    """
    user_request = state["messages"][-1].content
    raw_data_sample = pd.DataFrame(state["raw_data"]).head(3).to_string()
    
    system_prompt = f"""
    你是数据处理规划助手，根据用户需求和提供的数据样例，拆解为最多3个可执行的处理步骤，步骤可选范围：
    1. 数据清洗：去除空值、修正数据类型、删除重复行
    2. 统计计算：计算总和、平均值、最大值、TopN指标、分组统计等
    3. 结果分析：对统计结果做解读，输出可视化建议或业务结论
    数据样例：
    {raw_data_sample}
    用户需求：{user_request}
    仅返回JSON格式的步骤列表：{{"steps": ["步骤1", "步骤2", "步骤3"]}}
    """
    
    response = llm.invoke([system_prompt])
    plan = json.loads(response.content)
    
    return {
        **state,
        "process_steps": plan["steps"],
        "current_step": 0
    }

# ------------------------------
# 3. 数据清洗节点（行动模块：数据清洗操作）
# ------------------------------
def clean_data_node(state: DataProcessState) -> DataProcessState:
    """
    数据清洗节点功能：执行数据清洗操作，去除空值、重复项，修正数据类型
    """
    df = pd.DataFrame(state["raw_data"])
    # 标准清洗流程
    df = df.drop_duplicates()  # 去重
    df = df.dropna(subset=df.columns[df.isnull().mean() < 0.3])  # 删除空值占比<30%的行
    # 尝试转换数值列类型
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            pass
    
    return {
        **state,
        "cleaned_data": df.to_dict(orient="list"),
        "current_step": state["current_step"] + 1,
        "messages": state["messages"] + [AIMessage(content="已完成数据清洗，共去除{}条无效数据".format(len(state["raw_data"]) - len(df)))]
    }

# ------------------------------
# 4. 统计计算节点（行动模块：数据统计操作）
# ------------------------------
def calculate_stats_node(state: DataProcessState) -> DataProcessState:
    """
    统计计算节点功能：根据用户需求执行统计计算
    """
    df = pd.DataFrame(state["cleaned_data"] if state.get("cleaned_data") else state["raw_data"])
    user_request = state["messages"][-1].content
    
    system_prompt = f"""
    根据用户需求和数据字段，生成可直接执行的pandas计算代码，仅返回代码本身，不需要其他解释
    数据字段：{list(df.columns)}
    数据样例：{df.head(2).to_string()}
    用户需求：{user_request}
    代码执行结果需存储在result变量中，最后返回result.to_dict()格式
    """
    
    code_response = llm.invoke([system_prompt])
    # 执行生成的计算代码
    local_vars = {"df": df}
    exec(code_response.content, globals(), local_vars)
    stats_result = local_vars["result"]
    
    return {
        **state,
        "stats_result": stats_result,
        "current_step": state["current_step"] + 1,
        "messages": state["messages"] + [AIMessage(content="已完成统计计算")]
    }

# ------------------------------
# 5. 结果生成节点（行动模块：输出最终结果）
# ------------------------------
def generate_result_node(state: DataProcessState) -> DataProcessState:
    """
    结果生成节点功能：整合所有处理结果，生成自然语言分析报告
    """
    stats_result = state.get("stats_result", {})
    user_request = state["messages"][-1].content
    
    system_prompt = f"""
    根据统计结果，生成自然语言的分析报告回答用户需求
    用户需求：{user_request}
    统计结果：{json.dumps(stats_result, ensure_ascii=False, indent=2)}
    """
    
    response = llm.invoke([system_prompt])
    
    return {
        **state,
        "messages": state["messages"] + [response],
        "current_step": state["current_step"] + 1
    }

# ------------------------------
# 6. 路由逻辑：根据当前步骤选择下一个执行节点
# ------------------------------
def route_step(state: DataProcessState) -> str:
    if state["current_step"] >= len(state["process_steps"]):
        return END
    current_step = state["process_steps"][state["current_step"]]
    if "清洗" in current_step:
        return "clean"
    elif "计算" in current_step or "统计" in current_step:
        return "calculate"
    elif "分析" in current_step or "结果" in current_step:
        return "generate"
    else:
        return "generate"

# ------------------------------
# 7. 构建数据处理Agent
# ------------------------------
def build_data_process_agent():
    workflow = StateGraph(DataProcessState)
    
    # 添加节点
    workflow.add_node("plan", plan_process_node)
    workflow.add_node("clean", clean_data_node)
    workflow.add_node("calculate", calculate_stats_node)
    workflow.add_node("generate", generate_result_node)
    
    # 入口节点
    workflow.set_entry_point("plan")
    
    # 条件路由
    workflow.add_conditional_edges("plan", route_step)
    workflow.add_conditional_edges("clean", route_step)
    workflow.add_conditional_edges("calculate", route_step)
    workflow.add_edge("generate", END)
    
    return workflow.compile()

# ------------------------------
# 测试运行示例
# ------------------------------
if __name__ == "__main__":
    agent = build_data_process_agent()
    
    # 模拟用户上传的销售数据
    test_data = {
        "月份": ["1月", "2月", "3月", "4月", "5月", "6月"],
        "销售额": [12000, 15000, None, 18000, 22000, 22000],
        "产品": ["A", "B", "A", "C", "A", "B"]
    }
    
    # 用户需求
    test_request = "帮我统计各产品的总销售额，找出销售额最高的产品"
    
    initial_state = {
        "messages": [HumanMessage(content=test_request)],
        "raw_data": test_data,
        "cleaned_data": {},
        "stats_result": {},
        "process_steps": [],
        "current_step": 0
    }
    
    result = agent.invoke(initial_state)
    
    print("用户需求：", test_request)
    print("最终分析结果：", result["messages"][-1].content)
    print("\n完整执行链路：用户上传数据和需求 → 规划节点拆解步骤[清洗→计算→分析] → 依次执行清洗节点/计算节点 → 结果生成节点输出报告")
