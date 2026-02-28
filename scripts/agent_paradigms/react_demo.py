#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简ReAct范式Demo
核心逻辑：推理(Reasoning) <-> 动作(Acting) 交替执行
"""

# 模拟可用工具列表
available_tools = {
 "get_weather": lambda city: f"{city}今日天气：晴，25℃，风力2级",
 "get_time": lambda _: "当前时间：2024年6月15日 14:30"
}

def react_agent(user_query: str) -> str:
 """
 ReAct Agent核心执行函数
 :param user_query: 用户输入问题
 :return: 最终回答结果
 """
 max_step = 3
 current_step = 1
 observation = None

 while current_step <= max_step:
 print(f"\n===== 执行步骤 {current_step} =====")

 # 1. 推理环节：根据已有信息判断下一步动作
 if current_step == 1:
 thought = "用户询问北京今天是否适合郊游，我需要先获取北京今日天气数据，调用get_weather工具查询"
 action = {"tool": "get_weather", "param": "北京"}
 elif current_step == 2:
 thought = f"已获取天气信息：{observation}，晴天25℃非常适合郊游，无需继续调用工具，可以直接回答用户"
 action = None
 else:
 thought = "超出最大执行步数，直接返回结果"
 action = None

 print(f"【推理】{thought}")

 # 无后续动作直接返回结果
 if action is None:
 return "✅ 北京今日天气晴朗，气温25℃，非常适合外出郊游哦~"

 # 2. 动作环节：调用工具获取真实观测结果
 print(f"【动作】调用工具：{action['tool']}，参数：{action['param']}")
 observation = available_tools[action['tool']](action['param'])
 print(f"【观测】工具返回结果：{observation}")

 current_step += 1

if __name__ == "__main__":
 query = "北京今天适合去郊游吗？"
 print(f"用户问题：{query}")
 result = react_agent(query)
 print(f"\n最终回答：{result}")
