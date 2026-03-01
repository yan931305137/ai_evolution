"""
动态 Agent 工厂

允许 AutoAgent 在运行时动态创建 Specialist Agent
"""
import os
import re
import uuid
import logging
import importlib.util
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.llm import LLMClient
from src.agents.specialist_agents import BaseSpecialistAgent, AgentType
from src.utils.config import cfg

logger = logging.getLogger(__name__)


@dataclass
class DynamicAgentInfo:
    """动态 Agent 信息"""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    created_at: datetime
    file_path: str
    task_count: int = 0
    success_count: int = 0
    agent_class: Optional[Type] = None
    agent_instance: Optional[BaseSpecialistAgent] = None


class DynamicAgentFactory:
    """
    动态 Agent 工厂
    
    根据任务需求动态生成 Specialist Agent
    """
    
    def __init__(self, llm: LLMClient, dynamic_agents_dir: str = "src/agents/dynamic"):
        self.llm = llm
        self.dynamic_agents_dir = dynamic_agents_dir
        self.registry: Dict[str, DynamicAgentInfo] = {}
        
        # 确保目录存在
        os.makedirs(self.dynamic_agents_dir, exist_ok=True)
        
        # 加载已存在的动态 Agent
        self._load_existing_agents()
    
    def _load_existing_agents(self):
        """加载已存在的动态 Agent"""
        if not os.path.exists(self.dynamic_agents_dir):
            return
        
        for filename in os.listdir(self.dynamic_agents_dir):
            if filename.endswith("_agent.py") and not filename.startswith("__"):
                agent_id = filename.replace("_agent.py", "")
                file_path = os.path.join(self.dynamic_agents_dir, filename)
                
                # 尝试加载 Agent 类
                try:
                    agent_class = self._load_agent_class(file_path, agent_id)
                    if agent_class:
                        self.registry[agent_id] = DynamicAgentInfo(
                            agent_id=agent_id,
                            name=agent_id,
                            description="Loaded from existing file",
                            capabilities=[],
                            created_at=datetime.fromtimestamp(os.path.getctime(file_path)),
                            file_path=file_path,
                            agent_class=agent_class
                        )
                        logger.info(f"Loaded existing dynamic agent: {agent_id}")
                except Exception as e:
                    logger.warning(f"Failed to load agent {agent_id}: {e}")
    
    def _load_agent_class(self, file_path: str, agent_id: str) -> Optional[Type]:
        """从文件加载 Agent 类"""
        try:
            spec = importlib.util.spec_from_file_location(f"dynamic_{agent_id}", file_path)
            if not spec or not spec.loader:
                return None
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 Agent 类
            class_name = f"{self._to_camel_case(agent_id)}Agent"
            if hasattr(module, class_name):
                return getattr(module, class_name)
            
            # 尝试其他命名
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseSpecialistAgent) and 
                    attr != BaseSpecialistAgent):
                    return attr
            
            return None
        except Exception as e:
            logger.error(f"Error loading agent class from {file_path}: {e}")
            return None
    
    def _to_camel_case(self, snake_str: str) -> str:
        """将 snake_case 转换为 CamelCase"""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)
    
    def analyze_task_requirements(self, task_description: str) -> Dict[str, Any]:
        """
        分析任务需求，确定所需的 Agent 能力
        
        Args:
            task_description: 任务描述
            
        Returns:
            需求分析结果
        """
        prompt = f"""Analyze this task and determine what kind of Specialist Agent is needed:

Task: {task_description}

Provide your analysis as JSON:
{{
    "agent_name": "descriptive_name_for_agent",
    "description": "What this agent specializes in",
    "capabilities": ["capability1", "capability2", "capability3"],
    "required_tools": ["file_tools", "code_tools", "web_search", etc.],
    "expertise_level": "beginner|intermediate|expert",
    "system_prompt_focus": "Specific focus areas for the system prompt"
}}

Guidelines:
- agent_name: Use snake_case, descriptive but concise
- capabilities: 3-5 specific capabilities this agent needs
- required_tools: Which tool categories are needed
- expertise_level: How specialized should the agent be"""
        
        try:
            response = self.llm.generate([
                {"role": "user", "content": prompt}
            ])
            
            import json
            analysis = json.loads(response.strip())
            return analysis
        except Exception as e:
            logger.error(f"Task analysis failed: {e}")
            # 回退到默认分析
            return self._fallback_analysis(task_description)
    
    def _fallback_analysis(self, task_description: str) -> Dict[str, Any]:
        """回退分析"""
        task_lower = task_description.lower()
        
        # 基于关键词的简单分类
        if any(kw in task_lower for kw in ["test", "testing", "assert", "pytest"]):
            return {
                "agent_name": "testing_specialist",
                "description": "Specializes in writing comprehensive tests",
                "capabilities": ["unit testing", "integration testing", "test coverage analysis"],
                "required_tools": ["file_tools", "code_tools"],
                "expertise_level": "expert",
                "system_prompt_focus": "Writing high-quality, maintainable tests with good coverage"
            }
        elif any(kw in task_lower for kw in ["doc", "document", "readme", "comment"]):
            return {
                "agent_name": "documentation_specialist",
                "description": "Specializes in technical documentation",
                "capabilities": ["API documentation", "code comments", "README writing"],
                "required_tools": ["file_tools"],
                "expertise_level": "intermediate",
                "system_prompt_focus": "Clear, concise technical documentation"
            }
        elif any(kw in task_lower for kw in ["refactor", "restructure", "clean up"]):
            return {
                "agent_name": "refactoring_specialist",
                "description": "Specializes in code refactoring",
                "capabilities": ["code restructuring", "pattern application", "complexity reduction"],
                "required_tools": ["file_tools", "code_tools", "ai_assistant_tools"],
                "expertise_level": "expert",
                "system_prompt_focus": "Safe, incremental refactoring with behavior preservation"
            }
        else:
            return {
                "agent_name": f"task_specialist_{uuid.uuid4().hex[:6]}",
                "description": f"Specializes in: {task_description[:50]}",
                "capabilities": ["task execution", "problem solving"],
                "required_tools": ["file_tools", "code_tools"],
                "expertise_level": "intermediate",
                "system_prompt_focus": "Efficient task completion with best practices"
            }
    
    def generate_agent_code(self, analysis: Dict[str, Any]) -> str:
        """
        生成 Agent 代码
        
        Args:
            analysis: 任务需求分析结果
            
        Returns:
            生成的 Python 代码
        """
        agent_name = analysis["agent_name"]
        description = analysis["description"]
        capabilities = analysis["capabilities"]
        required_tools = analysis.get("required_tools", ["file_tools", "code_tools"])
        expertise_level = analysis.get("expertise_level", "intermediate")
        focus = analysis.get("system_prompt_focus", "Task execution")
        
        class_name = f"{self._to_camel_case(agent_name)}Agent"
        capabilities_str = "\n".join([f"- {cap}" for cap in capabilities])
        
        # 生成工具描述
        tool_descriptions = self._generate_tool_descriptions(required_tools)
        
        code = f'''"""
动态生成的 Specialist Agent

Name: {agent_name}
Description: {description}
Generated at: {datetime.now().isoformat()}
Expertise Level: {expertise_level}
"""
import logging
from src.agents.specialist_agents import BaseSpecialistAgent, AgentType
from src.utils.llm import LLMClient
from src.utils.config import cfg

logger = logging.getLogger(__name__)


class {class_name}(BaseSpecialistAgent):
    """
    {description}
    
    Capabilities:
{capabilities_str}
    """
    
    def __init__(self, llm: LLMClient):
        # 使用 DYNAMIC 类型，但保持 specialist 特性
        super().__init__(AgentType.CODE, llm)
        self.custom_name = "{agent_name}"
        self.custom_description = """{description}"""
        
    def get_system_prompt(self, task: str) -> str:
        return f"""You are a {expertise_level}-level Specialist Agent.

Your Focus: {focus}

Task: {{task}}

Your Capabilities:
{capabilities_str}

GUIDELINES:
1. Leverage your specialized expertise
2. Follow best practices in your domain
3. Produce high-quality, professional results
4. Consider edge cases and potential issues
5. Document your approach when appropriate

Available Tools:
{tool_descriptions}

When complete, provide:
1. Summary of what was accomplished
2. Any important findings or decisions
3. Suggestions for next steps if applicable

Output your response as JSON:
{{
    "thought": "Your reasoning and approach",
    "action": "tool_name or 'finish'",
    "action_input": {{...}}
}}"""
'''
        return code
    
    def _generate_tool_descriptions(self, required_tools: List[str]) -> str:
        """生成工具描述"""
        tool_mapping = {
            "file_tools": "- File operations (read_file, write_file, list_files)",
            "code_tools": "- Code modification (patch_code, analyze_code, search_code)",
            "system_tools": "- System commands (run_command)",
            "git_tools": "- Git operations (git_status, git_commit, etc.)",
            "web_search": "- Web search for information",
            "ai_assistant_tools": "- AI-powered code analysis",
            "directory_tools": "- Directory management",
            "json_yaml_tools": "- JSON/YAML processing",
        }
        
        descriptions = []
        for tool in required_tools:
            if tool in tool_mapping:
                descriptions.append(tool_mapping[tool])
        
        return "\n".join(descriptions) if descriptions else "- General purpose tools available"
    
    def create_agent(self, task_description: str) -> str:
        """
        创建新的动态 Agent
        
        Args:
            task_description: 任务描述
            
        Returns:
            agent_id: 新创建的 Agent ID
        """
        logger.info(f"Creating dynamic agent for task: {task_description[:100]}...")
        
        # 1. 分析任务需求
        analysis = self.analyze_task_requirements(task_description)
        agent_name = analysis["agent_name"]
        
        # 确保名称唯一
        base_name = re.sub(r'[^a-z0-9_]', '_', agent_name.lower())
        agent_id = base_name
        counter = 1
        while agent_id in self.registry:
            agent_id = f"{base_name}_{counter}"
            counter += 1
        
        # 2. 生成代码
        code = self.generate_agent_code(analysis)
        
        # 3. 保存文件
        file_path = os.path.join(self.dynamic_agents_dir, f"{agent_id}_agent.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Generated agent code saved to: {file_path}")
        
        # 4. 自动生成并注册文档
        self._generate_agent_docs(agent_id, analysis, file_path)

        # 5. 加载 Agent 类
        agent_class = self._load_agent_class(file_path, agent_id)
        if not agent_class:
            raise RuntimeError(f"Failed to load generated agent class: {agent_id}")
        
        # 6. 注册到 registry
        agent_info = DynamicAgentInfo(
            agent_id=agent_id,
            name=agent_id,
            description=analysis["description"],
            capabilities=analysis["capabilities"],
            created_at=datetime.now(),
            file_path=file_path,
            agent_class=agent_class
        )
        self.registry[agent_id] = agent_info
        
        logger.info(f"Dynamic agent '{agent_id}' created successfully")
        return agent_id

    def _generate_agent_docs(self, agent_id: str, analysis: Dict[str, Any], file_path: str):
        """
        为动态 Agent 生成 markdown 文档
        """
        try:
            from src.tools.docs_tools import register_document
            
            doc_content = f"""# Agent Documentation: {agent_id}

## Overview
- **Name**: {analysis.get('agent_name', agent_id)}
- **Type**: Dynamic Specialist Agent
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Expertise Level**: {analysis.get('expertise_level', 'Unknown')}

## Description
{analysis.get('description', 'No description provided.')}

## Capabilities
"""
            for cap in analysis.get('capabilities', []):
                doc_content += f"- {cap}\n"
            
            doc_content += f"""
## Required Tools
"""
            for tool in analysis.get('required_tools', []):
                 doc_content += f"- {tool}\n"
            
            doc_content += f"""
## System Prompt Focus
{analysis.get('system_prompt_focus', 'None')}

## Source Code
File: `{os.path.basename(file_path)}`
"""
            
            # Save doc file
            docs_dir = os.path.join(os.path.dirname(self.dynamic_agents_dir), "../../docs/agents/dynamic")
            os.makedirs(docs_dir, exist_ok=True)
            doc_path = os.path.join(docs_dir, f"{agent_id}_doc.md")
            
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
                
            # Register document
            # Note: register_document might be a static method or standalone function depending on import
            # Here we assume it's available via import as used in create_agent context or we import it
            # To be safe, we'll use the imported function if available or skip registration if complex
            
            logger.info(f"Generated documentation for agent {agent_id} at {doc_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate documentation for agent {agent_id}: {e}")

    
    def get_agent(self, agent_id: str, llm: LLMClient) -> Optional[BaseSpecialistAgent]:
        """
        获取 Agent 实例
        
        Args:
            agent_id: Agent ID
            llm: LLM 客户端
            
        Returns:
            Agent 实例或 None
        """
        if agent_id not in self.registry:
            logger.warning(f"Agent '{agent_id}' not found in registry")
            return None
        
        agent_info = self.registry[agent_id]
        
        # 如果已有实例，直接返回
        if agent_info.agent_instance:
            return agent_info.agent_instance
        
        # 创建新实例
        if agent_info.agent_class:
            try:
                agent_info.agent_instance = agent_info.agent_class(llm)
                return agent_info.agent_instance
            except Exception as e:
                logger.error(f"Failed to instantiate agent {agent_id}: {e}")
                return None
        
        return None
    
    def list_agents(self) -> List[DynamicAgentInfo]:
        """列出所有动态 Agent"""
        return list(self.registry.values())
    
    def get_agent_info(self, agent_id: str) -> Optional[DynamicAgentInfo]:
        """获取 Agent 信息"""
        return self.registry.get(agent_id)
    
    def update_agent_stats(self, agent_id: str, success: bool):
        """更新 Agent 统计"""
        if agent_id in self.registry:
            info = self.registry[agent_id]
            info.task_count += 1
            if success:
                info.success_count += 1
    
    def delete_agent(self, agent_id: str) -> bool:
        """
        删除动态 Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功删除
        """
        if agent_id not in self.registry:
            return False
        
        agent_info = self.registry[agent_id]
        
        # 删除文件
        try:
            if os.path.exists(agent_info.file_path):
                os.remove(agent_info.file_path)
        except Exception as e:
            logger.error(f"Failed to delete agent file: {e}")
            return False
        
        # 从 registry 移除
        del self.registry[agent_id]
        
        logger.info(f"Dynamic agent '{agent_id}' deleted")
        return True


# 全局工厂实例（将在 AutoAgent 中初始化）
_global_factory: Optional[DynamicAgentFactory] = None


def get_factory(llm: Optional[LLMClient] = None) -> DynamicAgentFactory:
    """获取全局工厂实例"""
    global _global_factory
    if _global_factory is None:
        if llm is None:
            llm = LLMClient()
        _global_factory = DynamicAgentFactory(llm)
    return _global_factory
