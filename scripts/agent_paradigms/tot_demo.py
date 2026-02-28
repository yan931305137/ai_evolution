#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简思维树(Tree of Thoughts, ToT)范式Demo
核心逻辑：多路径生成 -> 路径评估打分 -> 选择最优路径 -> 输出结果
"""

def generate_thought_paths(problem: str) -> list:
 """
 生成多个可能的推理路径
 :param problem: 待解决的问题：24点游戏，数字3,4,5,6
 :return: 候选推理路径列表
 """
 return [
 "路径1：3+4+5+6 = 18，不够24，错误",
 "路径2：6*5 - (4+3) = 30 -7 =23，差1，错误",
 "路径3：(3+5-4)*6 = 4 *6 =24，完全正确",
 "路径4：5*4 + (6-3) =20 +3=23，差1，错误"
 ]

def evaluate_path(path: str) -> int:
 """
 评估每个推理路径的得分（0-10分，越高越优）
 :param path: 待评估的推理路径
 :return: 得分
 """
 if "错误" in path:
 return 3
 elif "完全正确" in path:
 return 10
 else:
 return 5

def tot_agent(problem: str) -> str:
 """
 思维树Agent核心执行函数
 :param problem: 待解决问题
 :return: 最优解
 """
 print(f"待解决问题：{problem}\n")

 # 步骤1：生成多条候选推理路径
 print("【步骤1：生成候选推理路径】")
 paths = generate_thought_paths(problem)
 for p in paths:
 print(f"- {p}")

 # 步骤2：对每条路径打分评估
 print("\n【步骤2：评估路径得分】")
 scored_paths = [(evaluate_path(p), p) for p in paths]
 for score, p in scored_paths:
 print(f"得分{score}：{p}")

 # 步骤3：选择得分最高的路径作为最优解
 print("\n【步骤3：选择最优路径】")
 best_path = sorted(scored_paths, key=lambda x:x[0], reverse=True)[0][1]
 print(f"最优路径：{best_path}")

 return "\n✅ 24点解法：(3+5-4)*6 = 24"

if __name__ == "__main__":
 problem = "用数字3、4、5、6通过四则运算得到24，每个数字只能用一次"
 result = tot_agent(problem)
 print(result)
