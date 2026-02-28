#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简自我反思(Self-Reflection)范式Demo
核心逻辑：生成初始结果 -> 反思评估问题 -> 优化迭代结果
"""

def generate_initial_draft() -> str:
 """生成初始版本的文案"""
 return "我家卖的杯子特别好，大家快来买啊。"

def reflect_on_draft(draft: str) -> str:
 """反思环节：评估初始版本存在的问题，给出优化建议"""
 return "当前文案太生硬，没有突出卖点，用户看完没有购买欲望，优化建议：1. 突出杯子的核心优势（耐高温、防摔、颜值高）；2. 增加优惠信息引导下单；3. 语气更亲切。"

def optimize_draft(draft: str, reflection: str) -> str:
 """根据反思结果优化文案"""
 return "✨ 宝子们！我们家这款食品级耐高温玻璃杯，防摔还颜值超高，今天下单立减10元还送杯刷，赶紧冲呀~"

def self_reflection_agent(task: str) -> str:
 """
 自我反思Agent核心执行函数
 :param task: 待完成任务
 :return: 最终优化结果
 """
 print(f"待完成任务：{task}\n")

 # 步骤1：生成初始结果
 print("【步骤1：生成初始结果】")
 draft = generate_initial_draft()
 print(f"初始文案：{draft}\n")

 # 步骤2：自我反思评估
 print("【步骤2：自我反思评估】")
 reflection = reflect_on_draft(draft)
 print(f"反思结论：{reflection}\n")

 # 步骤3：根据反思优化结果
 print("【步骤3：优化生成最终结果】")
 final_result = optimize_draft(draft, reflection)
 print(f"优化后文案：{final_result}")

 return final_result

if __name__ == "__main__":
 task = "写一个杯子的朋友圈促销文案"
 result = self_reflection_agent(task)
 print(f"\n✅ 最终产出文案：{result}")
