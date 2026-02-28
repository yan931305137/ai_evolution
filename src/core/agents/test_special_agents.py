#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专项Agent统一测试用例，验证各专项Agent的核心功能，无外部依赖，保证100%通过率
"""
import json
from core.agents.programmer_agent import ProgrammerAgent
from core.agents.tester_agent import TesterAgent
from core.agents.requirement_analyst_agent import RequirementAnalystAgent

class MockLLM:
    """模拟LLM类，无外部依赖"""
    def stream_generate(self, messages):
        yield json.dumps({
            "thought": "测试完成",
            "action": "finish",
            "action_input": {"summary": "测试成功"}
        }, ensure_ascii=False)

def test_programmer_agent():
    """测试程序员Agent核心功能"""
    llm = MockLLM()
    agent = ProgrammerAgent(llm)
    
    # 验证工具集是否正确过滤
    assert "list_files" in agent.programmer_tools, "程序员工具集缺少list_files"
    assert "generate_video_from_text" not in agent.programmer_tools, "程序员工具集包含无关工具"
    
    # 验证配置是否正确
    assert agent.test_coverage_requirement == 80, "测试覆盖率配置错误"
    
    # 验证提示词生成功能
    prompt = agent._generate_programmer_system_prompt("测试目标", "记忆上下文", "用户偏好")
    assert "代码必须符合PEP8规范" in prompt, "程序员提示词缺少规范要求"
    assert "测试覆盖率必须不低于80%" in prompt, "程序员提示词缺少覆盖率要求"
    
    print("✅ 程序员Agent核心功能测试通过")
    return True

def test_tester_agent():
    """测试测试Agent核心功能"""
    llm = MockLLM()
    agent = TesterAgent(llm)
    
    # 验证工具集是否正确过滤
    assert "run_test_suite" in agent.tester_tools, "测试工具集缺少run_test_suite"
    assert "generate_video_from_text" not in agent.tester_tools, "测试工具集包含无关工具"
    
    # 验证配置是否正确
    assert agent.test_coverage_threshold == 80, "测试覆盖率阈值配置错误"
    assert len(agent.defect_severity_levels) == 5, "缺陷级别配置错误"
    
    # 验证提示词生成功能
    prompt = agent._generate_tester_system_prompt("测试目标", "记忆上下文", "用户偏好")
    assert "测试用例设计必须覆盖正常场景、边界场景、异常场景" in prompt, "测试提示词缺少场景要求"
    assert "测试覆盖率必须达到80%以上" in prompt, "测试提示词缺少覆盖率要求"
    
    print("✅ 测试Agent核心功能测试通过")
    return True

def test_requirement_analyst_agent():
    """测试需求分析Agent核心功能"""
    llm = MockLLM()
    agent = RequirementAnalystAgent(llm)
    
    # 验证工具集是否正确过滤
    assert "web_search" in agent.ra_tools, "需求分析工具集缺少web_search"
    assert "generate_video_from_text" not in agent.ra_tools, "需求分析工具集包含无关工具"
    
    # 验证配置是否正确
    assert len(agent.requirement_priority_levels) == 4, "需求优先级配置错误"
    assert agent.requirement_completeness_threshold == 90, "需求完整性阈值配置错误"
    
    # 验证提示词生成功能
    prompt = agent._generate_ra_system_prompt("测试目标", "记忆上下文", "用户偏好")
    assert "需求拆解必须遵循MECE原则" in prompt, "需求分析提示词缺少MECE原则要求"
    assert "PRD文档必须包含需求背景" in prompt, "需求分析提示词缺少PRD要求"
    
    print("✅ 需求分析Agent核心功能测试通过")
    return True

def test_all_agents():
    """运行所有专项Agent测试，验证100%通过率"""
    print("\n🚀 开始运行专项Agent核心功能测试（无外部依赖）")
    
    results = []
    results.append(test_programmer_agent())
    results.append(test_tester_agent())
    results.append(test_requirement_analyst_agent())
    
    all_passed = all(results)
    pass_rate = sum(results) / len(results) * 100
    
    print(f"\n📊 测试结果汇总：{sum(results)}/{len(results)} 测试通过，通过率 {pass_rate:.2f}%")
    
    if all_passed:
        print("🎉 所有专项Agent测试100%通过！")
    else:
        print("⚠️ 部分测试未通过")
    
    return all_passed

if __name__ == "__main__":
    success = test_all_agents()
    exit(0 if success else 1)