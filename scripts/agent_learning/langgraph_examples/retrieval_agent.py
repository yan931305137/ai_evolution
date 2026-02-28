#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangGraph信息检索Agent示例
功能：接收用户问题，自主判断是否需要调用搜索工具获取信息，整合后返回准确回答
执行链路：用户输入 → 感知模块解析问题 → 规划模块判断是否需要搜索 → 行动模块调用搜索工具(如需) → 结果整合 → 返回回答
"""

# 导入所需依赖包
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
import os
from dotenv import load_dotenv

# 加载环境变量（需要提前配置OPENAI_API_KEY和TAVILY_API_KEY）
load_dotenv()

# 初始化大模型和搜索工具
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ------------------------------
# 1. 定义Agent状态（记忆模块核心存储结构）
# ------------------------------
class AgentState(TypedDict):
    # 消息列表：存储对话历史、工具返回结果等所有上下文信息（对应短期记忆）
    messages: Sequence[BaseMessage]
    # 标记是否需要执行搜索动作（规划模块输出的决策结果）
    need_search: bool
    # 存储搜索到的信息（行动模块输出的中间结果）
    search_result: str

# ------------------------------
# 2. 定义规划节点（对应规划模块功能）
# ------------------------------
def plan_node(state: AgentState) -> AgentState:
    """
    规划节点功能：接收当前状态，判断用户问题是否需要调用搜索工具获取最新信息
    """
    messages = state["messages"]
    
    # 构造系统提示，指导大模型判断是否需要搜索
    system_prompt = SystemMessage(content="""
    你是一个智能决策助手，判断用户的问题是否需要调用搜索工具获取最新信息才能回答：
    1. 如果问题涉及实时信息、最新事件、需要外部数据支撑，请返回need_search=True
    2. 如果问题是常识性问题、不需要最新信息即可回答，请返回need_search=False
    输出格式仅返回JSON：{"need_search": true/false}
    """)
    
    # 调用大模型进行决策
    response = llm.invoke([system_prompt] + messages)
    import json
    decision = json.loads(response.content)
    
    # 更新状态中的决策结果
    return {
        **state,
        "need_search": decision["need_search"]
    }

# ------------------------------
# 3. 定义检索节点（对应行动模块的工具调用功能）
# ------------------------------
def search_node(state: AgentState) -> AgentState:
    """
    检索节点功能：调用Tavily搜索工具获取用户问题相关的最新信息
    """
    user_query = state["messages"][-1].content
    
    # 调用搜索工具，获取前3条相关结果
    search_response = tavily.search(query=user_query, max_results=3)
    search_result = "\n".join([item["content"] for item in search_response["results"]])
    
    # 更新状态中的搜索结果
    return {
        **state,
        "search_result": search_result,
        "messages": state["messages"] + [AIMessage(content=f"已获取搜索信息：{search_result[:100]}...")]
    }

# ------------------------------
# 4. 定义回答生成节点（对应行动模块的结果输出功能）
# ------------------------------
def answer_node(state: AgentState) -> AgentState:
    """
    回答生成节点功能：整合上下文和搜索结果（如有），生成最终回答返回给用户
    """
    messages = state["messages"]
    search_result = state.get("search_result", "")
    
    # 构造回答提示
    if search_result:
        prompt_content = f"基于以下搜索信息回答用户问题：\n搜索信息：{search_result}\n用户问题：{messages[-1].content}"
    else:
        prompt_content = f"回答用户问题：{messages[-1].content}"
    
    response = llm.invoke([SystemMessage(content=prompt_content)])
    
    # 更新状态，添加最终回答
    return {
        **state,
        "messages": messages + [response]
    }

# ------------------------------
# 5. 定义路由逻辑（连接各节点的流转规则）
# ------------------------------
def route_after_plan(state: AgentState) -> str:
    """
    规划节点后的路由：根据决策结果选择下一个执行节点
    """
    if state["need_search"]:
        return "search"  # 需要搜索则进入检索节点
    else:
        return "answer"  # 不需要搜索则直接进入回答节点

# ------------------------------
# 6. 构建Agent执行图（核心协作逻辑组装）
# ------------------------------
def build_retrieval_agent():
    # 初始化状态图
    workflow = StateGraph(AgentState)
    
    # 添加所有节点到图中
    workflow.add_node("plan", plan_node)      # 规划节点
    workflow.add_node("search", search_node)  # 检索节点
    workflow.add_node("answer", answer_node)  # 回答节点
    
    # 设置入口节点（最先执行的节点）
    workflow.set_entry_point("plan")
    
    # 添加条件边：规划节点完成后根据路由规则选择下一个节点
    workflow.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "search": "search",
            "answer": "answer"
        }
    )
    
    # 添加普通边：检索节点完成后进入回答节点
    workflow.add_edge("search", "answer")
    # 添加结束边：回答节点完成后结束执行
    workflow.add_edge("answer", END)
    
    # 编译图为可执行的Agent
    return workflow.compile()

# ------------------------------
# 测试运行示例
# ------------------------------
if __name__ == "__main__":
    # 构建Agent
    agent = build_retrieval_agent()
    
    # 测试问题1：需要实时搜索的问题
    test_query = "2024年中国GDP同比增长率是多少？"
    initial_state = {
        "messages": [HumanMessage(content=test_query)],
        "need_search": False,
        "search_result": ""
    }
    
    # 执行Agent
    result = agent.invoke(initial_state)
    
    # 输出结果
    print("用户问题：", test_query)
    print("最终回答：", result["messages"][-1].content)
    print("\n完整执行链路：用户输入 → 规划节点判断需要搜索 → 检索节点调用Tavily获取数据 → 回答节点整合结果输出")
