import os
import sys
import argparse
import logging
# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load environment variables before importing core modules that might initialize systems
load_dotenv()

# Force HF_ENDPOINT if not set, to ensure users in China can download models
if "HF_ENDPOINT" not in os.environ:
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from src.utils.config import cfg
from src.storage.database import Database
from src.utils.llm import LLMClient

from src.agents.agent import AutoAgent
from src.utils.enhanced_lifecycle import EnhancedLifeCycleManager
import threading
# 导入热重载管理器
from src.utils.hot_reload_manager import hot_reload_manager

# 冒烟测试函数：验证核心服务基础功能正常
def core_smoke_test():
    """核心功能冒烟测试，热重载后自动执行，确保100%功能可用"""
    try:
        # 测试LLM客户端初始化正常
        llm = hot_reload_manager.get_module_instance('src.utils.llm')
        if not llm or not hasattr(llm, 'stream_generate'):
            logging.error("LLM 模块冒烟测试失败: 缺少 stream_generate 方法")
            return False
        
        # 测试数据库模块正常
        db = hot_reload_manager.get_module_instance('src.storage.database')
        if not db or not hasattr(db, 'save_conversation'):
            logging.error("Database 模块冒烟测试失败: 缺少 save_conversation 方法")
            return False
        
        # 测试Agent模块正常
        agent = hot_reload_manager.get_module_instance('src.agents.agent')
        if not agent or not hasattr(agent, 'run'):
            logging.error("Agent 模块冒烟测试失败: 缺少 run 方法")
            return False
        
        # 测试生命周期管理器正常
        lifecycle = hot_reload_manager.get_module_instance('src.utils.enhanced_lifecycle')
        if lifecycle and not hasattr(lifecycle, 'get_status'):
            logging.error("Lifecycle 模块冒烟测试失败: 缺少 get_status 方法")
            return False
        
        # 测试 Self-Awareness 模块（如果已注册）
        awareness = hot_reload_manager.get_module_instance('src.utils.self_awareness')
        if awareness and not hasattr(awareness, 'record_capability_usage'):
            logging.warning("Self-Awareness 模块冒烟测试警告: 缺少 record_capability_usage 方法")
        
        # 测试 Memory 模块（如果已注册）
        memory = hot_reload_manager.get_module_instance('src.storage.memory')
        if memory and not hasattr(memory, 'retrieve'):
            logging.warning("Memory 模块冒烟测试警告: 缺少 retrieve 方法")
        
        logging.info("✅ 核心系统冒烟测试通过")
        return True
        
    except Exception as e:
        logging.error(f"冒烟测试执行失败: {str(e)}", exc_info=True)
        return False

# Initialize Rich Console
console = Console()

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_environment():
    load_dotenv()
    cfg.load()
    
def main():
    """Main entry point for OpenClaw-Local CLI."""
    setup_logging()
    load_environment()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='OpenClaw-Local 自主进化AI代理')
    parser.add_argument('--self-evolution', action='store_true', help='直接启动自主进化闭环运行模式，无需人工交互')
    args = parser.parse_args()
    
    console.print("[bold green]Welcome to OpenClaw-Local (Doubao Evolution Edition)![/bold green]")
    console.print("[dim]Type '/exit' to quit, '/agent' for manual task, '/auto' to toggle autonomy, '/evolve' to start self-evolution closed loop.[/dim]")
    
    # Initialize Core Components
    db = Database()
    llm = LLMClient()
    agent = AutoAgent(llm)
    personality_type = cfg.get("personality.type", "balanced")
    lifecycle = EnhancedLifeCycleManager(llm, db, personality_type=personality_type)
    
    # 注册核心模块到热重载管理器
    hot_reload_manager.register_module('src.storage.database', db)
    hot_reload_manager.register_module('src.utils.llm', llm)
    hot_reload_manager.register_module('src.agents.agent', agent)
    hot_reload_manager.register_module('src.utils.enhanced_lifecycle', lifecycle)
    
    # 注册冒烟测试
    hot_reload_manager.register_smoke_test(core_smoke_test)
    
    # 函数：从热重载管理器获取最新模块实例
    def get_module(name):
        return hot_reload_manager.get_module_instance(name)
    
    # 如果指定了自主进化参数，直接启动闭环运行
    if args.self_evolution:
        console.print("[bold green]已启用自主进化闭环运行模式，将自动进行连续迭代优化...[/bold green]")
        agent.continuous_run()
        return
    
    # Check if API Key is set
    if not llm.api_key or llm.api_key == "YOUR_API_KEY_HERE":
        console.print("[bold red]Error: API Key not configured![/bold red]")
        console.print("Please edit [bold]config/config.yaml[/bold] or set [bold]DOUBAO_API_KEY[/bold] environment variable.")
        return

    # Conversation Loop
    history: List[Dict[str, str]] = [
        {"role": "system", "content": "You are OpenClaw, an advanced local AI assistant. Your goal is to help the user with tasks on their local computer.\n"
                                      "If the user asks to perform a complex task, suggest using '/agent <task>' mode.\n"
                                      "Always be concise and helpful."}
    ]
    last_response_id = None
    
    while True:
        try:
            # Update prompt to show status
            status_text = ""
            if lifecycle.running:
                status_text = f" [AUTO: {lifecycle.state} | {lifecycle.needs.get_status()}]"
                
            user_input = Prompt.ask(f"\n[bold cyan]You{status_text}[/bold cyan]")
            
            if user_input.lower() in ('/exit', '/quit'):
                lifecycle.stop()
                break
                
            if user_input.lower().startswith('/auto'):
                if lifecycle.running:
                    lifecycle.stop()
                else:
                    # Check if user provided a goal in the same line
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        goal = parts[1].strip()
                    else:
                        goal = Prompt.ask("[bold yellow]Set a long-term goal for me[/bold yellow]", default=lifecycle.long_term_goal)
                    
                    lifecycle.set_goal(goal)
                    lifecycle.start()
                continue
                
            if user_input.lower() == '/evolve':
                console.print("[bold green]启动自主进化闭环运行模式，将自动识别能力缺口、规划迭代路径并持续优化，无需人工干预...[/bold green]")
                agent.continuous_run()
                continue
                
            if user_input.lower() == '/status':
                console.print(f"[bold yellow]{lifecycle.get_status()}[/bold yellow]")
                continue

            if user_input.lower().startswith('/agent '):
                goal = user_input[7:].strip()
                if not goal:
                    console.print("[yellow]Please provide a goal. Usage: /agent <your goal>[/yellow]")
                    continue
                
                console.print(f"[bold magenta]Starting Auto-Agent for goal:[/bold magenta] {goal}")
                agent.run(goal)
                continue
                
            if user_input.lower() == '/feedback':
                if last_response_id:
                    feedback = Prompt.ask("Enter feedback (e.g., 'Good', 'Bad', or corrected text)")
                    rating = Prompt.ask("Rate (1-5)", default="0")
                    db.update_feedback(last_response_id, feedback, int(rating))
                    console.print("[green]Feedback saved![/green]")
                else:
                    console.print("[yellow]No recent response to rate.[/yellow]")
                continue
                
            if not user_input.strip():
                continue

            # Add to history
            history.append({"role": "user", "content": user_input})
            
            # Streaming Response
            console.print("\n[bold purple]OpenClaw (Doubao)[/bold purple]: ", end="")
            full_response = ""
            
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots") as status:
                stream = llm.stream_generate(history)
                # First chunk to break the status spinner
                try:
                    first_chunk = next(stream)
                    status.stop()
                    console.print(first_chunk, end="")
                    full_response += first_chunk
                except StopIteration:
                    status.stop()
            
            # Print remaining chunks
            for chunk in stream:
                console.print(chunk, end="")
                full_response += chunk
                
            console.print() # Newline
            
            # Add to history
            history.append({"role": "assistant", "content": full_response})
            
            # Save to Database (Crucial for Evolution)
            last_response_id = db.save_conversation(
                input_text=user_input,
                output_text=full_response,
                instruction="General Chat", # Can be inferred later
                model_used=llm.model_name
            )
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting...[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            logging.error(f"Runtime error: {e}")

if __name__ == "__main__":
    main()
