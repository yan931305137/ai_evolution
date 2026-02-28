#!/usr/bin/env python3
"""
多 Agent 系统演示脚本

展示多 Agent 协调系统的基本功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_banner():
    """打印欢迎横幅"""
    console.print(Panel.fit(
        "[bold blue]🤖 Multi-Agent System Demo[/bold blue]\n"
        "[dim]Intelligent task coordination with specialist agents[/dim]",
        border_style="blue"
    ))


def demo_mode_selection():
    """演示模式选择逻辑"""
    console.print("\n[bold yellow]📊 Task Complexity Assessment[/bold yellow]")
    
    from src.agents.multi_agent import MultiAgentRunner
    
    runner = MultiAgentRunner(api_key='demo-key')
    
    test_cases = [
        ("修复 utils.py 中的拼写错误", "简单修改"),
        ("添加用户登录功能", "功能实现"),
        ("重构认证模块并添加测试和文档", "复杂重构"),
        ("设计并实现全新的支付系统架构", "架构设计"),
    ]
    
    table = Table(title="Mode Selection Results")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Complexity", justify="center")
    table.add_column("Selected Mode", style="green")
    
    for goal, description in test_cases:
        complexity = runner._assess_complexity(goal)
        use_multi = runner._should_use_multi_agent(goal, None)
        mode = "🤖 Multi-Agent" if use_multi else "🤖 Single-Agent"
        
        table.add_row(
            description,
            f"{complexity}/10",
            mode
        )
    
    console.print(table)


def demo_task_decomposition():
    """演示任务分解"""
    console.print("\n[bold yellow]🔨 Task Decomposition Example[/bold yellow]")
    
    # 模拟复杂任务的分解
    console.print("[dim]Complex Task:[/dim] 重构认证模块并添加测试和文档")
    console.print()
    
    subtasks = [
        ("1", "分析", "🔍 分析当前认证模块的代码结构和依赖关系", [], "analyze"),
        ("2", "重构", "🔧 重构认证模块，提取公共逻辑，消除重复代码", ["1"], "refactor"),
        ("3", "测试", "🧪 为重构后的认证模块编写单元测试和集成测试", ["2"], "test"),
        ("4", "审查", "👀 审查重构后的代码和测试覆盖情况", ["2", "3"], "review"),
        ("5", "文档", "📝 更新认证模块的 API 文档和使用说明", ["4"], "doc"),
    ]
    
    for task_id, agent_type, desc, deps, icon in subtasks:
        dep_str = f" (depends: {', '.join(deps)})" if deps else " (no dependencies)"
        console.print(f"  [{agent_type:8}] {desc}{dep_str}")
    
    console.print()
    console.print("[dim]Execution Order:[/dim] 1 → 2 → 3 & 4 (parallel) → 5")


def demo_agent_types():
    """演示 Agent 类型"""
    console.print("\n[bold yellow]👥 Available Specialist Agents[/bold yellow]")
    
    from src.agents.specialist_agents import AgentType
    
    agents = [
        (AgentType.CODE, "💻", "Code Development", "编写和修改代码"),
        (AgentType.TEST, "🧪", "Testing", "编写测试用例"),
        (AgentType.DOC, "📝", "Documentation", "生成技术文档"),
        (AgentType.REVIEW, "👀", "Code Review", "代码审查"),
        (AgentType.ANALYZE, "🔍", "Analysis", "代码结构分析"),
        (AgentType.REFACTOR, "🔧", "Refactoring", "代码重构"),
        (AgentType.DEBUG, "🐛", "Debugging", "Bug 排查"),
    ]
    
    table = Table()
    table.add_column("Agent", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    
    for agent_type, icon, name, desc in agents:
        table.add_row(f"{icon} {agent_type.value}", name, desc)
    
    console.print(table)


def demo_execution_modes():
    """演示执行模式"""
    console.print("\n[bold yellow]⚙️ Execution Modes[/bold yellow]")
    
    modes = [
        ("Sequential", "顺序执行", "任务 A → 任务 B → 任务 C", "有依赖关系的任务"),
        ("Parallel", "并行执行", "任务 A | 任务 B | 任务 C", "完全独立的任务"),
        ("Hybrid", "混合模式", "智能调度依赖关系", "默认，最常用"),
    ]
    
    table = Table()
    table.add_column("Mode", style="cyan")
    table.add_column("Execution Flow")
    table.add_column("Best For")
    
    for mode, flow, visual, best_for in modes:
        table.add_row(f"{mode}", visual, best_for)
    
    console.print(table)


def demo_code_example():
    """演示代码示例"""
    console.print("\n[bold yellow]💡 Usage Examples[/bold yellow]")
    
    code = '''
# 1. 自动模式（推荐）
from src.agents.multi_agent import run_sync

result = run_sync("重构认证模块，添加测试和文档")

# 2. 强制多 Agent 模式
result = run_sync("分析项目", mode="multi")

# 3. 强制单 Agent 模式
result = run_sync("简单修改", mode="single")

# 4. 使用特定 Specialist Agent
import asyncio
from src.agents.multi_agent import run_specialist

result = asyncio.run(run_specialist("review", "审查 auth.py"))
'''
    
    console.print(Panel(code, title="Python API", border_style="green"))


def main():
    """主函数"""
    print_banner()
    
    try:
        demo_mode_selection()
        demo_task_decomposition()
        demo_agent_types()
        demo_execution_modes()
        demo_code_example()
        
        console.print("\n" + "="*60)
        console.print("[bold green]✓ Demo completed![/bold green]")
        console.print("[dim]Run with a real task:[/dim]")
        console.print("  python -m src.agents.multi_agent \"你的任务描述\"")
        console.print("="*60)
        
    except Exception as e:
        console.print(f"\n[red]Error during demo: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
