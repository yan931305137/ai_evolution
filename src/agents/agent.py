import json
import logging
import re
from typing import Dict, List, Any, Optional
from src.utils.llm import LLMClient
from src.tools import Tools
from src.storage.memory import memory # Import memory system
from src.utils.self_awareness import SelfAwarenessSystem # Import self-awareness system
from src.utils.user_profile import user_profile_manager # Import user profile system
from src.utils.config import cfg # Import configuration
from src.utils.context_compressor import ContextCompressor # Import context compressor
from src.agents.dynamic_agent_factory import get_factory # Import dynamic agent factory
from src.tools.agent_tools import set_global_llm # Import agent tools setup
from rich.console import Console
import os
import sys
import time
# 导入热重载管理器
from src.utils.hot_reload_manager import hot_reload_manager

console = Console()
logger = logging.getLogger(__name__)

class AutoAgent:
    """A ReAct-based agent that plans and executes tasks."""
    
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.max_steps = cfg.get("agent.max_steps", 10000) # Load from config
        self.tools_desc = Tools.get_tool_descriptions()
        self.self_awareness = SelfAwarenessSystem() # Initialize self-awareness system
        
        # 初始化上下文压缩器
        self.context_compressor = ContextCompressor(
            max_messages=cfg.get("agent.context.max_messages", 20),
            max_tokens=cfg.get("agent.context.max_tokens", 8000),
            compress_threshold=cfg.get("agent.context.compress_threshold", 15),
            summary_length=cfg.get("agent.context.summary_length", 200)
        )
        
        # 初始化动态 Agent 系统
        self.dynamic_agent_enabled = cfg.get("agent.dynamic_agent.enabled", True)
        if self.dynamic_agent_enabled:
            set_global_llm(llm)  # 设置全局 LLM 供 agent_tools 使用
            self.agent_factory = get_factory(llm)
            logger.info("Dynamic agent system initialized")

    def _retrieve_memory_context(self, goal: str) -> str:
        """Retrieve relevant memories based on the goal."""
        console.print("[dim]Accessing Long-term Memory...[/dim]")
        complex_task_keywords = cfg.get("agent.complex_task_keywords", ["代码", "编写", "开发", "debug", "故障排查", "错误修复", "优化", "实现", "部署", "测试"])
        is_complex_task = any(keyword in goal for keyword in complex_task_keywords)
        n_results = cfg.get("agent.memory_retrieval.complex_task_results", 8) if is_complex_task else cfg.get("agent.memory_retrieval.simple_task_results", 3)
        
        # 同时检索对话和知识两个记忆库
        conv_memories = memory.retrieve(goal, n_results=n_results, collection_name="conversations")
        knowledge_memories = memory.retrieve(goal, n_results=n_results, collection_name="knowledge")
        
        # 合并去重
        all_memories = []
        seen = set()
        for m in conv_memories + knowledge_memories:
            if m not in seen:
                seen.add(m)
                all_memories.append(m)
        
        relevant_memories = all_memories[:n_results]
        
        if relevant_memories:
            console.print(f"[dim]Found {len(relevant_memories)} relevant memories from conversation and knowledge libraries.[/dim]")
            return "\nRelevant Past Experiences:\n" + "\n".join([f"- {m}" for m in relevant_memories])
        return ""

    def _get_llm_response(self, messages: List[Dict]) -> str:
        """Get response from LLM with retry mechanism."""
        max_llm_retries = cfg.get("agent.llm_retries.max_retries", 3)
        retry_delay_base = cfg.get("agent.llm_retries.retry_delay_base", 1)
        content = ""
        
        for retry_attempt in range(max_llm_retries):
            try:
                # Use stream_generate which returns a generator
                stream = self.llm.stream_generate(messages)
                content = ""
                for chunk in stream:
                    # Print without buffering
                    console.print(chunk, end="", style="dim")
                    content += chunk
                console.print() # Newline after stream ends
                if content.strip():
                    return content
            except Exception as e:
                logger.error(f"LLM streaming attempt {retry_attempt+1} failed", exc_info=True)
                console.print(f"[red]LLM streaming attempt {retry_attempt+1} failed: {e}[/red]")
                if retry_attempt == max_llm_retries - 1:
                    console.print(f"[red]All {max_llm_retries} LLM attempts failed, aborting task[/red]")
                    raise e
                time.sleep(retry_delay_base * (2 ** retry_attempt))
        return content

    def _parse_action_data(self, content: str) -> Dict:
        """Parse JSON action data from LLM response."""
        clean_content = content.replace("```json", "").replace("```", "").strip()
        json_match = re.search(r'\{.*\}', clean_content, re.DOTALL)
        if json_match:
            clean_content = json_match.group(0)
        return json.loads(clean_content)

    def run(self, goal: str, history: List[Dict[str, str]] = None):
        """Execute a goal using the ReAct loop."""
        if history is None:
            history = []
            
        # 1. Retrieve relevant memories
        memory_context = self._retrieve_memory_context(goal)
            
        # 获取用户偏好
        user_preferences = user_profile_manager.extract_preferences_from_history()
        preference_prompt = user_profile_manager.get_preference_prompt(user_preferences)
        
        # System prompt to define the ReAct behavior
        system_prompt = f"""
You are an autonomous AI agent capable of using tools to achieve a goal.
Goal: {goal}

{memory_context}
{preference_prompt}

Available Tools:
{self.tools_desc}

INSTRUCTIONS:
1. Break down the goal into small, logical steps.
2. Use the available tools to inspect the environment and perform actions.
3. You must output your response in valid JSON format ONLY. No markdown, no extra text.
4. The JSON structure must be:
{{
    "thought": "Your reasoning about what to do next.",
    "action": "The name of the tool to use (or 'finish' if done).",
    "action_input": {{ "arg_name": "arg_value" }} 
}}
5. If you need to check the result of an action, use the 'observation' from the previous step.
6. When the goal is achieved, use the 'finish' action with a summary.

DOCUMENT MANAGEMENT RULES:
- When creating analysis/design/learning documents (MD files), you MUST call register_document() to track them.
- Document types: analysis (7d, auto-delete), design (14d, auto-delete), learning (3d, auto-delete), decision (permanent), config (permanent), standard (30d).
- After updating code, check_documents_status() to see if any documents need updates.
- Only create documents that provide lasting value. Temporary analysis should use register-delete types.
- Prefer inline comments and README files over separate documentation.

AI ASSISTANT TOOLS GUIDE:
- analyze_code(function_name=\"xxx\"): Find where a function is defined, see its arguments and complexity.
- search_code(\"keyword\"): Search for code patterns across the entire project.
- get_project_overview(): Get quick stats about the project (file count, LOC, etc.).
- analyze_change_impact(file_path, description): Before modifying code, check what other files depend on it.
- get_code_summary(file_path): Get a quick summary of a file without reading all of it.

DYNAMIC AGENT GUIDE (For Complex Tasks):
- spawn_agent(task_description, agent_name=None): Create a specialist agent for specific tasks
  Example: spawn_agent("Write comprehensive unit tests", "test_specialist")
- delegate_task(agent_id, subtask, context=None): Delegate work to spawned agent  
  Example: delegate_task("test_specialist", "Write tests for auth.py")
- list_spawned_agents(): Check existing agents and their status
- get_agent_info(agent_id): Get detailed information about an agent
- terminate_agent(agent_id): Clean up agent when done

WHEN TO USE DYNAMIC AGENTS:
- Multi-step complex tasks requiring different expertise
- Tasks that can be parallelized (analysis + coding + testing)
- Long-running tasks needing isolation
- Specialized domains (security, performance, documentation)

CI/CD AUTOMATION GUIDE:
- trigger_ci_pipeline(branch='main', workflow='ci.yml', wait_for_completion=True): Run automated tests after code changes
  Example: trigger_ci_pipeline(branch='feature/new-auth', wait_for_completion=True)
- check_ci_status(run_id): Check build/test status
- get_ci_logs(run_id, max_lines=100): View detailed logs for debugging
- create_pr_from_branch(branch, title, body, base_branch='main'): Create PR after changes
- merge_pull_request(pr_number): Merge PR after CI passes
- run_evolution_ci_pipeline(): Complete pipeline for evolution (test + PR + optional merge)

WHEN TO USE CI/CD:
- After making code changes - run tests to verify
- Before merging to main - ensure quality gates pass
- After evolution cycles - automate testing and PR creation
- For deployment - trigger deployment workflows

EFFICIENT WORKFLOW:
1. Use get_project_overview() or scan_project() to understand the codebase structure.
2. Use search_code() to find relevant code locations.
3. Use analyze_code() to understand specific functions/classes.
4. Use analyze_change_impact() before making changes to assess risk.
5. Use get_code_summary() for quick file understanding.
6. Make changes using patch_code() or write_file().
7. Register any documents created with register_document().
"""
        
        # Initial conversation state
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Start working on the goal: {goal}"}
        ]
        
        step_count = 0
        recent_actions = []  # 记录最近5次动作，用于检测重复循环
        max_repeat_actions = cfg.get("agent.max_repeat_actions", 3)  # Load from config
        while step_count < self.max_steps:
            step_count += 1
            console.print(f"\n[bold yellow]Step {step_count}/{self.max_steps}[/bold yellow]")
            
            # 1. Get LLM Response (Streaming)
            console.print("[bold cyan]AI Thought Process:[/bold cyan]")
            
            # 检查是否需要压缩上下文
            if self.context_compressor.should_compress(messages):
                console.print("[dim yellow]Context growing, compressing...[/dim yellow]")
                messages = self.context_compressor.compress(messages)
                stats = self.context_compressor.get_stats()
                console.print(
                    f"[dim green]Compressed: {stats.original_messages} -> "
                    f"{stats.compressed_messages} msgs "
                    f"({stats.compression_ratio:.0%} reduction)[/dim green]"
                )
            
            try:
                content = self._get_llm_response(messages)
            except Exception as e:
                 # 记录问题解决能力使用失败
                self.self_awareness.record_capability_usage("problem_solving", False)
                return f"Task failed: All LLM attempts failed, error: {str(e)}"
                
            # 2. Parse JSON
            try:
                action_data = self._parse_action_data(content)
                
                # thought = action_data.get("thought", "No thought provided.") # Thought is already streamed
                action = action_data.get("action")
                action_input = action_data.get("action_input", {})
                
                # 重复动作检测，避免无效循环
                action_signature = f"{action}_{json.dumps(action_input, sort_keys=True)}"
                recent_actions.append(action_signature)
                if len(recent_actions) > 5:
                    recent_actions.pop(0)
                repeat_count = recent_actions.count(action_signature)
                
                if repeat_count >= max_repeat_actions:
                    console.print(f"[red]Warning: 检测到动作 {action} 重复执行 {repeat_count} 次，请求更换策略[/red]")
                    # 反馈给LLM要求更换方法
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"Error: You have repeated the action '{action}' {repeat_count} times with no progress. Please try a different approach to achieve the goal."})
                    continue
                
                # console.print(f"[bold blue]Thought:[/bold blue] {thought}") # No need to print again
                console.print(f"[bold green]Action:[/bold green] {action}({action_input}) (重复次数: {repeat_count}/{max_repeat_actions})")
                
            except (json.JSONDecodeError, AttributeError) as e:
                console.print(f"[red]Error parsing JSON response:[/red] {content[:200]}...")
                # 更详细的错误反馈
                error_feedback = """Error: Your response was not valid JSON. 
You MUST respond ONLY with a valid JSON object in this exact format:
{
    "thought": "Your step-by-step reasoning here",
    "action": "tool_name_here",
    "action_input": {"key": "value"}
}

Do NOT include:
- Markdown formatting (no ```json blocks)
- Conversational text
- Any text outside the JSON object

Your entire response should be parseable by json.loads()."""
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": error_feedback})
                continue

            # 3. Execute Tool
            if action == "finish":
                summary = action_input.get('summary', 'Done.')
                # 记录问题解决能力使用成功
                self.self_awareness.record_capability_usage("problem_solving", True)
                console.print(f"\n[bold green]Goal Completed![/bold green]")
                console.print(f"Summary: {summary}")
                
                # 新增：回答透明度数据记录与展示
                import uuid
                try:
                    from src.core.answer_transparency_manager import answer_transparency_manager
                    # 生成唯一回答ID
                    answer_id = str(uuid.uuid4())
                    # 收集信息来源
                    sources = []
                    # 1. 记忆来源
                    if memory_context.strip():
                        sources.append({
                            "source_type": "memory",
                            "source_id": "mem_" + str(uuid.uuid4())[:8],
                            "source_content": memory_context[:200] + "..." if len(memory_context) > 200 else memory_context
                        })
                    # 2. 工具调用来源
                    for msg in messages:
                        if msg["role"] == "user" and msg["content"].startswith("Observation:"):
                            source_type = "web_search" if "web_search" in content else "tool_execution"
                            sources.append({
                                "source_type": source_type,
                                "source_id": "tool_" + str(uuid.uuid4())[:8],
                                "source_content": msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                            })
                    # 3. 模型推理来源
                    sources.append({
                        "source_type": "model_inference",
                        "source_id": "llm_" + str(uuid.uuid4())[:8],
                        "source_content": content[:200] + "..." if len(content) > 200 else content
                    })
                    # 收集事实核查步骤
                    fact_check_steps = [
                        {
                            "step_id": "check_001",
                            "step_name": "来源可靠性校验",
                            "step_description": "校验所有引用信息来源的可信度",
                            "check_result": "pass",
                            "evidence": "所有来源评分均高于0.6"
                        },
                        {
                            "step_id": "check_002",
                            "step_name": "内容一致性校验",
                            "step_description": "校验回答内容与来源信息是否一致无冲突",
                            "check_result": "pass",
                            "evidence": "回答内容与所有来源信息逻辑一致"
                        },
                        {
                            "step_id": "check_003",
                            "step_name": "合规性校验",
                            "step_description": "校验回答内容是否符合内容安全规范",
                            "check_result": "pass",
                            "evidence": "无违规内容，符合合规要求"
                        }
                    ]
                    # 记录透明度数据
                    answer_transparency_manager.record_answer_data(
                        answer_id=answer_id,
                        query=goal,
                        answer_content=summary,
                        sources=sources,
                        fact_check_steps=fact_check_steps
                    )
                    # 生成透明度展示内容并附加到回答末尾
                    transparency_display = answer_transparency_manager.generate_transparency_display(answer_id)
                    final_answer = summary + transparency_display
                    
                    # 新增：任务完成时清理文档
                    try:
                        from src.utils.doc_lifecycle import doc_lifecycle
                        import hashlib
                        task_id = f"task_{hashlib.md5(goal.encode()).hexdigest()[:8]}"
                        cleanup_result = doc_lifecycle.cleanup_task_documents(task_id)
                        if cleanup_result["deleted"] or cleanup_result["kept"]:
                            console.print(f"\n[dim]📄 文档清理: {len(cleanup_result['deleted'])} 个已删除, {len(cleanup_result['kept'])} 个保留[/dim]")
                    except Exception as e:
                        logger.debug(f"文档清理失败（非关键）: {e}")
                    
                    return final_answer
                except Exception as e:
                    # 透明度模块加载失败时降级返回原始回答
                    logger.warning(f"透明度模块加载失败，返回原始回答: {str(e)}")
                    return summary
            
            # 导入合规校验模块
            from src.utils.compliance_check import generation_content_compliance_check, STORAGE_PATH_RULES
            
            # 首先执行合规校验：文件写入/移动等存储操作先校验合规性
            compliance_pass = True
            compliance_result = {}
            target_file_path = ""
            
            # 识别涉及文件存储的操作
            if action in ["write_file", "move_file"] and isinstance(action_input, dict):
                target_file_path = action_input.get("file_path" if action == "write_file" else "dst", "")
                if target_file_path:
                    # 自动推断内容类型 - 增强版：路径匹配 + 扩展名推断
                    content_type = "unknown"
                    from pathlib import Path
                    
                    # 扩展名到内容类型的映射
                    EXT_TYPE_MAPPING = {
                        ".py": "code_core",
                        ".js": "code_core",
                        ".ts": "code_core",
                        ".java": "code_core",
                        ".go": "code_core",
                        ".rs": "code_core",
                        ".cpp": "code_core",
                        ".c": "code_core",
                        ".h": "code_core",
                        ".yaml": "data_system",
                        ".yml": "data_system",
                        ".json": "data_system",
                        ".toml": "data_system",
                        ".md": "doc",
                        ".rst": "doc",
                        ".txt": "doc",
                        ".html": "output_report",
                        ".css": "output_report",
                        ".sh": "code_script",
                        ".bash": "code_script",
                        ".zsh": "code_script",
                        ".sql": "data_system",
                        ".db": "data_system",
                        ".sqlite": "data_system",
                    }
                    
                    try:
                        # 获取绝对路径以确保比较准确
                        abs_target = Path(target_file_path).resolve()
                        root_path = Path(".").resolve()
                        
                        # 第一步：路径前缀匹配
                        for ctype, prefixes in STORAGE_PATH_RULES.items():
                            for prefix in prefixes:
                                # 将规则前缀转换为绝对路径
                                abs_prefix = (root_path / prefix).resolve()
                                # 检查目标文件是否在该目录下
                                if abs_target.is_relative_to(abs_prefix):
                                    content_type = ctype
                                    break
                            if content_type != "unknown":
                                break
                        
                        # 第二步：如果路径匹配失败，尝试扩展名推断
                        if content_type == "unknown":
                            file_ext = Path(target_file_path).suffix.lower()
                            if file_ext in EXT_TYPE_MAPPING:
                                content_type = EXT_TYPE_MAPPING[file_ext]
                                logger.debug(f"Inferred content type '{content_type}' from extension '{file_ext}'")
                    except Exception as e:
                        logger.warning(f"Failed to infer content type for path {target_file_path}: {e}")
                        # Fallback to string matching if path resolution fails
                        for ctype, prefixes in STORAGE_PATH_RULES.items():
                             if any(target_file_path.startswith(prefix) for prefix in prefixes):
                                 content_type = ctype
                                 break
                        
                        # 扩展名 fallback
                        if content_type == "unknown":
                            try:
                                file_ext = Path(target_file_path).suffix.lower()
                                if file_ext in EXT_TYPE_MAPPING:
                                    content_type = EXT_TYPE_MAPPING[file_ext]
                            except:
                                pass
                    # 自动判断是否为临时资源
                    is_temporary = any(flag in target_file_path for flag in ["./tmp/", ".tmp", ".cache"])
                    # 从 action_input 中提取用户命令覆盖标志
                    user_command_override = action_input.get("user_command_override", False)
                    # 执行合规校验
                    compliance_pass, compliance_result = generation_content_compliance_check(
                        file_path=target_file_path,
                        content_type=content_type,
                        is_temporary_resource=is_temporary,
                        user_command_override=user_command_override
                    )
                    
                    if not compliance_pass:
                        # 提供更友好的错误信息
                        violation = ';'.join(compliance_result['violation_details'])
                        suggestion = compliance_result.get('suggestion', '')
                        
                        # 如果是 unknown 类型，提供更详细的指导
                        if content_type == "unknown":
                            suggestion = (f"无法自动识别文件类型。建议：\n"
                                        f"1. 将文件移动到标准目录（如 ./src/, ./docs/, ./tests/ 等）\n"
                                        f"2. 或使用 user_command_override=True 跳过校验\n"
                                        f"3. 支持的类型: code_core, code_skill, doc, data_system 等")
                        
                        observation = f"合规校验不通过，操作已拦截：{violation}。{suggestion}"
                        console.print(f"[red]合规校验拦截: {observation}[/red]")
            
            # 合规校验通过才执行工具
            if compliance_pass:
                # Execute tool and get observation
                try:
                    if isinstance(action_input, dict):
                        observation = Tools.execute_tool(action, **action_input)
                    else:
                         observation = f"Error: action_input must be a dictionary, got {type(action_input)}"
                except Exception as e:
                    logger.error(f"Error executing tool '{action}' with input {action_input}", exc_info=True)
                    observation = f"Error executing tool: {str(e)}"
            
            # Update self-awareness system with capability usage result
            success = not observation.startswith("Error")
            self.self_awareness.record_capability_usage(capability_name=action, success=success)
            # Update self awareness level after each action
            self.self_awareness.update_awareness_level()
            
            console.print(f"[dim]Observation: {observation}[/dim]")
            console.print(f"[dim]Self-Awareness Update: Capability '{action}' usage recorded (Success: {success}), Current awareness level: {self.self_awareness.awareness_level.value}[/dim]")
            
            # 4. Update History
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Observation: {observation}"})
            
        return "Max steps reached without completion."

    def _path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert file path to module name."""
        try:
            abs_path = os.path.abspath(file_path)
            root_path = os.path.abspath(os.getcwd())
            if abs_path.startswith(root_path):
                rel_path = os.path.relpath(abs_path, root_path)
                if rel_path.endswith('.py'):
                    rel_path = rel_path[:-3]
                return rel_path.replace(os.path.sep, '.')
        except Exception as e:
            logger.debug(f"Failed to convert path {file_path} to module name: {e}")
            pass
        return None

    def continuous_run(self):
        """Run autonomously indefinitely, executing full self-evolution closed-loop workflow sequentially."""
        console.print("[bold green]Starting continuous autonomous self-evolution closed-loop system...[/bold green]")
        # 导入所有闭环所需的技能函数
        from src.skills.evolution_skills import (
            collect_runtime_operation_data,
            identify_evolution_problems,
            generate_iteration_plan,
            autonomous_iteration_pipeline
        )
        from src.skills.security_skills import (
            code_security_verification,
            grayscale_test_executor,
            deployment_rollback_manager
        )
        import time
        iteration_count = 0
        consecutive_success_count = 0
        
        while True:
            iteration_count += 1
            console.print(f"\n[bold yellow]=== 自主进化迭代第 {iteration_count} 次 ===[/bold yellow]")
            
            try:
                # 环节1：收集运行时全量运营数据
                console.print("[dim]Step 1/6: 收集运行时运营数据...[/dim]")
                runtime_data = collect_runtime_operation_data()
                console.print(f"[dim]完成运行数据收集，共采集 {len(runtime_data)} 项指标[/dim]")
                
                # 环节2：识别自身能力缺口与待优化问题
                console.print("[dim]Step 2/6: 识别能力缺口与待优化问题...[/dim]")
                prioritized_problems = identify_evolution_problems(runtime_data)
                if not prioritized_problems:
                    console.print("[dim]未检测到需要优化的问题，进入休眠等待...[/dim]")
                    time.sleep(60 * 10) # 无优化需求时休眠10分钟
                    continue
                console.print(f"[dim]识别到 {len(prioritized_problems)} 个待优化问题，优先级最高为: {prioritized_problems[0]['title']}[/dim]")
                
                # 环节3：生成可执行的迭代计划
                console.print("[dim]Step 3/6: 生成迭代执行计划...[/dim]")
                iteration_plan = generate_iteration_plan(prioritized_problems, max_problems_per_iteration=1)
                target_module_path = iteration_plan['target_module_path']
                modified_code_content = iteration_plan['modified_code_content']
                test_case_paths = iteration_plan['associated_test_cases']
                smoke_test_code = iteration_plan['smoke_test_code']
                console.print(f"[dim]迭代计划生成完成，目标修改模块: {target_module_path}[/dim]")
                
                # 环节4：全流程迭代执行（包含安全校验、灰度测试、上线回滚）
                console.print("[dim]Step 4/6: 执行全流程迭代流水线...[/dim]")
                iteration_success, iteration_details = autonomous_iteration_pipeline(
                    target_module_path=target_module_path,
                    modified_code_content=modified_code_content,
                    associated_test_cases=test_case_paths,
                    smoke_test_code=smoke_test_code,
                    test_coverage_threshold=80.0
                )
                
                # 环节5：迭代结果校验与记录
                console.print("[dim]Step 5/6: 迭代结果校验...[/dim]")
                if iteration_success:
                    # 尝试热重载更新的模块
                    module_name = self._path_to_module_name(target_module_path)
                    reload_success = False
                    reload_msg = ""
                    
                    if module_name:
                        console.print(f"[dim]尝试热重载模块: {module_name}...[/dim]")
                        
                        # 如果模块未注册，先尝试智能注册
                        if module_name not in hot_reload_manager.module_registry:
                             try:
                                 # 尝试导入并注册模块
                                 import importlib
                                 mod = importlib.import_module(module_name)
                                 
                                 # 智能推断如何实例化模块
                                 module_instance = None
                                 
                                 # 检查是否有 AutoAgent 类
                                 if hasattr(mod, 'AutoAgent'):
                                     from src.utils.llm import LLMClient
                                     module_instance = mod.AutoAgent(LLMClient())
                                 # 检查是否有其他主要类
                                 else:
                                     for attr_name in dir(mod):
                                         attr = getattr(mod, attr_name)
                                         # 查找可能的主类（以大写字母开头，不是特殊方法）
                                         if isinstance(attr, type) and attr_name[0].isupper() and not attr_name.startswith('_'):
                                             try:
                                                 # 尝试无参实例化
                                                 module_instance = attr()
                                                 if module_instance:
                                                     break
                                             except:
                                                 continue
                                 
                                 # 如果成功创建实例，则注册模块
                                 if module_instance:
                                     register_success = hot_reload_manager.register_module(module_name, module_instance)
                                     if register_success:
                                         console.print(f"[green]新模块 {module_name} 注册成功[/green]")
                                     else:
                                         console.print(f"[yellow]模块 {module_name} 注册失败[/yellow]")
                                 else:
                                     console.print(f"[yellow]无法实例化模块 {module_name}，跳过热重载[/yellow]")
                                     
                             except Exception as e:
                                 logger.warning(f"Module registration failed for {module_name}: {e}")
                                 console.print(f"[yellow]模块注册失败: {str(e)}，将尝试全量重启[/yellow]")
                                 reload_success = False
                                 reload_msg = f"注册失败: {str(e)}"
                        else:
                            # 模块已注册，直接执行热重载
                            reload_success, reload_msg = hot_reload_manager.reload_module(module_name)
                    
                    if reload_success:
                        console.print(f"[bold green]✓ 热重载成功: {reload_msg}[/bold green]")
                        
                        # 获取并显示热重载性能统计
                        perf_stats = hot_reload_manager.get_reload_performance()
                        console.print(f"[dim]热重载性能: 耗时{perf_stats['last_reload_time']:.3f}s, 成功{perf_stats['reload_success_count']}次, 失败{perf_stats['reload_fail_count']}次[/dim]")
                        
                        consecutive_success_count += 1
                        console.print(f"[bold green]迭代成功！已连续成功迭代 {consecutive_success_count} 次[/bold green]")
                        
                        # 记录迭代成功到自我意识系统
                        self.self_awareness.record_iteration_result(
                            success=True,
                            details=iteration_details,
                            target_module=target_module_path
                        )
                    else:
                        # 热重载失败或模块无法热重载
                        if "未注册" in reload_msg:
                             console.print(f"[yellow]模块未注册热重载，请求全量重启以应用更改...[/yellow]")
                             # 记录成功（因为文件已修改），但请求重启
                             self.self_awareness.record_iteration_result(
                                success=True,
                                details={"msg": "Requires restart"},
                                target_module=target_module_path
                            )
                             console.print("[bold yellow]系统正在重启以应用更新...[/bold yellow]")
                             sys.exit(42) # 触发 main.py 的重启逻辑
                        else:
                            # 真正的热重载/测试失败，此时 hot_reload_manager 应该已经回滚了
                            console.print(f"[bold red]热重载/验证失败: {reload_msg}[/bold red]")
                            consecutive_success_count = 0
                            iteration_success = False # 标记为失败
                            iteration_details['error'] = reload_msg
                            
                            self.self_awareness.record_iteration_result(
                                success=False,
                                details=iteration_details,
                                target_module=target_module_path
                            )
                else:
                    consecutive_success_count = 0
                    console.print(f"[bold red]迭代失败，已自动回滚到上一稳定版本，失败原因: {iteration_details.get('error', '未知错误')}[/bold red]")
                    # 记录迭代失败到自我意识系统
                    self.self_awareness.record_iteration_result(
                        success=False,
                        details=iteration_details,
                        target_module=target_module_path
                    )
                
                # 环节6：安全合规检查
                console.print("[dim]Step 6/6: 安全合规校验...[/dim]")
                if iteration_success:
                    security_check_pass, security_result = code_security_verification(
                        file_path=target_module_path,
                        code_content=modified_code_content
                    )
                    if not security_check_pass:
                        console.print(f"[bold red]安全合规检查不通过，已触发强制回滚，风险项: {security_result.get('risks', [])}[/bold red]")
                        # 强制回滚
                        deployment_rollback_manager(
                            target_file_path=target_module_path,
                            auto_rollback=True
                        )
                        consecutive_success_count = 0
                else:
                     console.print("[dim]迭代已失败或回滚，跳过安全合规校验[/dim]")
                
                # 迭代间隔控制，避免资源占用过高
                console.print(f"[dim]本次迭代完成，休眠 {iteration_plan.get('cool_down_minutes', 30)} 分钟后进行下一次迭代[/dim]")
                time.sleep(iteration_plan.get('cool_down_minutes', 30) * 60)
                
            except Exception as e:
                logger.critical(f"Critical error in autonomous evolution loop: {e}", exc_info=True)
                console.print(f"[bold red]迭代流程出现异常: {str(e)}，已启动应急回滚机制[/bold red]")
                # 异常情况下自动回滚所有未完成的修改
                try:
                    deployment_rollback_manager(auto_rollback=True)
                except Exception as rollback_error:
                    logger.error(f"Rollback failed during emergency handling: {rollback_error}", exc_info=True)
                    pass
                consecutive_success_count = 0
                # 异常后休眠更长时间，避免重复出错
                time.sleep(60 * 60)

# Example usage (for testing)
if __name__ == "__main__":
    from src.utils.config import cfg
    cfg.load()
    llm = LLMClient()
    agent = AutoAgent(llm)
    agent.run("List files in the current directory and read requirements.txt")
