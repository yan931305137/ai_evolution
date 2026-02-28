#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专项Agent能力矩阵统一管理模块
功能：管理所有专项Agent的注册、调度、能力查询、测试验证，形成统一的Agent能力矩阵
"""
import json
from typing import Dict, List, Any, Optional, Type
from src.agents.agent import AutoAgent
from src.utils.llm import LLMClient
from rich.console import Console

console = Console()

class AgentMatrixManager:
    """专项Agent能力矩阵管理器"""
    
    def __init__(self, llm: LLMClient = None):
        self.llm = llm if llm else LLMClient()
        # 已注册的专项Agent字典：{agent_type: agent_class}
        self.registered_agents: Dict[str, Type[AutoAgent]] = {}
        # 已实例化的Agent缓存
        self.agent_instances: Dict[str, AutoAgent] = {}
        # Agent能力描述字典
        self.agent_capabilities: Dict[str, List[str]] = {}
        
        # 初始化时自动注册所有内置专项Agent
        self._register_builtin_agents()
        
    def _register_builtin_agents(self):
        """注册所有内置专项Agent"""
        # 导入各专项Agent
        from core.agents.programmer_agent import ProgrammerAgent
        from core.agents.tester_agent import TesterAgent
        from core.agents.requirement_analyst_agent import RequirementAnalystAgent
        
        # 注册程序员Agent
        self.register_agent(
            agent_type="programmer",
            agent_class=ProgrammerAgent,
            capabilities=[
                "代码编写", "代码调试", "代码优化", "代码评审", "需求转代码",
                "单元测试生成", "架构设计", "安全漏洞修复"
            ]
        )
        
        # 注册测试Agent
        self.register_agent(
            agent_type="tester",
            agent_class=TesterAgent,
            capabilities=[
                "测试用例生成", "自动化测试执行", "测试覆盖率分析", "缺陷定位",
                "缺陷分析", "测试报告生成", "性能测试", "安全测试"
            ]
        )
        
        # 注册需求分析Agent
        self.register_agent(
            agent_type="requirement_analyst",
            agent_class=RequirementAnalystAgent,
            capabilities=[
                "需求拆解", "需求评审", "需求合理性校验", "优先级评估",
                "PRD文档生成", "需求转开发任务", "业务流程梳理"
            ]
        )
        
        console.print("[green]✅ 所有内置专项Agent注册完成[/green]")
    
    def register_agent(self, agent_type: str, agent_class: Type[AutoAgent], capabilities: List[str]):
        """
        注册新的专项Agent
        :param agent_type: Agent类型标识
        :param agent_class: Agent类
        :param capabilities: Agent能力描述列表
        """
        self.registered_agents[agent_type] = agent_class
        self.agent_capabilities[agent_type] = capabilities
        console.print(f"[green]✅ 成功注册专项Agent: {agent_type}[/green]")
    
    def get_agent(self, agent_type: str) -> Optional[AutoAgent]:
        """
        获取指定类型的Agent实例
        :param agent_type: Agent类型标识
        :return: Agent实例，不存在则返回None
        """
        if agent_type not in self.registered_agents:
            console.print(f"[red]❌ 未找到指定类型的Agent: {agent_type}[/red]")
            return None
        
        # 缓存实例，避免重复创建
        if agent_type not in self.agent_instances:
            self.agent_instances[agent_type] = self.registered_agents[agent_type](self.llm)
        
        return self.agent_instances[agent_type]
    
    def get_all_agent_types(self) -> List[str]:
        """获取所有已注册的Agent类型列表"""
        return list(self.registered_agents.keys())
    
    def get_agent_capabilities(self, agent_type: str) -> Optional[List[str]]:
        """获取指定Agent的能力列表"""
        return self.agent_capabilities.get(agent_type)
    
    def dispatch_task(self, task_type: str, task_goal: str, **kwargs) -> Optional[str]:
        """
        根据任务类型自动调度合适的Agent执行任务
        :param task_type: 任务类型：programmer/test/requirement等
        :param task_goal: 任务目标
        :param kwargs: 其他参数
        :return: 任务执行结果
        """
        agent_type_map = {
            "code": "programmer",
            "development": "programmer",
            "programming": "programmer",
            "test": "tester",
            "testing": "tester",
            "qa": "tester",
            "requirement": "requirement_analyst",
            "demand": "requirement_analyst",
            "analysis": "requirement_analyst"
        }
        
        # 匹配Agent类型
        matched_agent_type = agent_type_map.get(task_type.lower())
        if not matched_agent_type:
            console.print(f"[red]❌ 未找到匹配的Agent处理任务类型: {task_type}[/red]")
            return None
        
        agent = self.get_agent(matched_agent_type)
        if not agent:
            return None
        
        console.print(f"[blue]ℹ️ 调度[{matched_agent_type}]Agent执行任务: {task_goal}[/blue]")
        return agent.run(task_goal, **kwargs)
    
    def run_all_agent_tests(self) -> Dict[str, bool]:
        """
        运行所有专项Agent的场景模拟测试
        :return: 测试结果字典：{agent_type: 是否通过}
        """
        console.print("\n[bold yellow]🚀 开始运行所有专项Agent场景模拟测试[/bold yellow]")
        test_results = {}
        
        # 导入各Agent的测试函数
        from core.agents.programmer_agent import test_programmer_agent
        from core.agents.tester_agent import test_tester_agent
        from core.agents.requirement_analyst_agent import test_requirement_analyst_agent
        
        # 运行程序员Agent测试
        console.print("\n[bold cyan]🧪 运行程序员Agent测试...[/bold cyan]")
        try:
            test_results["programmer"] = test_programmer_agent()
        except Exception as e:
            console.print(f"[red]❌ 程序员Agent测试失败: {str(e)}[/red]")
            test_results["programmer"] = False
        
        # 运行测试Agent测试
        console.print("\n[bold cyan]🧪 运行测试Agent测试...[/bold cyan]")
        try:
            test_results["tester"] = test_tester_agent()
        except Exception as e:
            console.print(f"[red]❌ 测试Agent测试失败: {str(e)}[/red]")
            test_results["tester"] = False
        
        # 运行需求分析Agent测试
        console.print("\n[bold cyan]🧪 运行需求分析Agent测试...[/bold cyan]")
        try:
            test_results["requirement_analyst"] = test_requirement_analyst_agent()
        except Exception as e:
            console.print(f"[red]❌ 需求分析Agent测试失败: {str(e)}[/red]")
            test_results["requirement_analyst"] = False
        
        # 汇总测试结果
        console.print("\n[bold yellow]📊 专项Agent测试结果汇总[/bold yellow]")
        pass_count = sum(1 for res in test_results.values() if res)
        total_count = len(test_results)
        pass_rate = (pass_count / total_count) * 100
        
        for agent_type, passed in test_results.items():
            status = "✅ 通过" if passed else "❌ 失败"
            console.print(f"{agent_type}: {status}")
        
        console.print(f"\n[bold green]总通过率: {pass_count}/{total_count} ({pass_rate:.2f}%)[/bold green]")
        
        return test_results


# 能力矩阵初始化与测试入口
def init_agent_matrix() -> AgentMatrixManager:
    """初始化专项Agent能力矩阵"""
    matrix = AgentMatrixManager()
    console.print("[green]✅ 专项Agent能力矩阵初始化完成[/green]")
    return matrix


def main():
    """主函数：初始化能力矩阵并运行所有测试"""
    # 初始化能力矩阵
    matrix = init_agent_matrix()
    
    # 运行所有Agent测试
    test_results = matrix.run_all_agent_tests()
    
    # 验证通过率100%
    all_passed = all(test_results.values())
    if all_passed:
        console.print("\n[bold green]🎉 所有专项Agent场景模拟测试通过率100%，里程碑2目标达成！[/bold green]")
    else:
        console.print("\n[bold red]⚠️ 部分Agent测试未通过，请检查修复后重新运行测试[/bold red]")


if __name__ == "__main__":
    main()