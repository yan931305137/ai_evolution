#!/usr/bin/env python3
"""
智能任务执行优化器 (Smart Task Executor)

核心功能：
1. 任务复杂度智能评估
2. 自动选择 Brain 本地处理或 LLM 调用
3. 执行路径优化
4. 自我学习和改进

目标：将简单任务的 LLM 调用减少 70%+
"""

import re
import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import lru_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """执行模式"""
    LOCAL_ONLY = "local_only"      # 仅本地处理（Brain）
    LOCAL_FIRST = "local_first"    # 优先本地，不确定时转 LLM
    HYBRID = "hybrid"              # 混合模式
    LLM_FIRST = "llm_first"        # 优先 LLM


@dataclass
class TaskProfile:
    """任务画像"""
    task_id: str
    goal: str
    complexity_score: float  # 0-1，越高越复杂
    estimated_tokens: int
    suggested_mode: ExecutionMode
    cache_key: str
    similar_tasks: List[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    content: str
    mode_used: ExecutionMode
    llm_calls: int
    brain_calls: int
    duration_ms: float
    cached: bool = False


class IntentClassifier:
    """意图分类器 - 本地处理简单意图"""
    
    # 意图模式定义
    PATTERNS = {
        # 信息查询类 - 简单，本地处理
        "git_status": {
            "patterns": [r"git\s+status", r"查看.*git.*状态", r"git状态"],
            "complexity": 0.1,
            "handler": "local"
        },
        "git_log": {
            "patterns": [r"git\s+log", r"查看.*提交.*历史", r"提交记录"],
            "complexity": 0.1,
            "handler": "local"
        },
        "list_files": {
            "patterns": [r"列出.*文件", r"显示.*目录", r"ls\s", r"dir\s"],
            "complexity": 0.1,
            "handler": "local"
        },
        "read_file": {
            "patterns": [r"读取.*文件", r"查看.*内容", r"cat\s", r"显示.*代码"],
            "complexity": 0.2,
            "handler": "local"
        },
        
        # 问候类 - 本地模板回复
        "greeting": {
            "patterns": [r"^hello", r"^hi", r"^你好", r"^在吗", r"^在么"],
            "complexity": 0.0,
            "handler": "template"
        },
        "help": {
            "patterns": [r"^help", r"帮助", r"怎么用", r"能做什么"],
            "complexity": 0.1,
            "handler": "template"
        },
        
        # 代码分析类 - 中等复杂度
        "code_review": {
            "patterns": [r"review", r"代码审查", r"检查.*代码", r"分析.*代码"],
            "complexity": 0.5,
            "handler": "hybrid"
        },
        
        # 开发类 - 复杂，需要 LLM
        "code_generate": {
            "patterns": [r"编写", r"实现", r"创建.*功能", r"开发", r"写.*代码"],
            "complexity": 0.8,
            "handler": "llm"
        },
        "refactor": {
            "patterns": [r"重构", r"优化", r"改进", r"rewrite"],
            "complexity": 0.7,
            "handler": "llm"
        },
        "design": {
            "patterns": [r"设计", r"架构", r"方案", r"plan"],
            "complexity": 0.9,
            "handler": "llm"
        },
        
        # 调试类 - 中等偏复杂
        "debug": {
            "patterns": [r"debug", r"调试", r"修复.*bug", r"错误", r"error"],
            "complexity": 0.6,
            "handler": "hybrid"
        },
        
        # 测试类
        "test": {
            "patterns": [r"测试", r"test", r"unittest", r"pytest"],
            "complexity": 0.5,
            "handler": "hybrid"
        },
    }
    
    def classify(self, goal: str) -> Tuple[str, float, str]:
        """
        分类意图
        
        Returns:
            (intent_type, complexity, handler_type)
        """
        goal_lower = goal.lower().strip()
        
        for intent_name, config in self.PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, goal_lower, re.IGNORECASE):
                    return intent_name, config["complexity"], config["handler"]
        
        # 默认未知意图，中等复杂度
        return "unknown", 0.5, "hybrid"


class TemplateResponder:
    """模板响应器 - 本地快速回复"""
    
    TEMPLATES = {
        "greeting": [
            "你好！我是 OpenClaw，有什么可以帮助你的吗？",
            "Hi！有什么我可以协助的吗？",
            "你好！准备好开始工作了吗？",
        ],
        "help": [
            """我可以帮你：
• 代码开发、重构、调试
• 文件操作和系统管理
• 项目分析和优化建议
• 自动化任务执行

输入你的需求即可开始！""",
        ],
        "git_help": [
            """Git 相关命令：
• git status - 查看状态
• git log - 查看历史
• git diff - 查看变更
• git add/commit/push - 提交代码

需要具体帮助吗？""",
        ],
    }
    
    def respond(self, intent: str, context: Dict = None) -> Optional[str]:
        """根据意图返回模板响应"""
        import random
        
        if intent in self.TEMPLATES:
            templates = self.TEMPLATES[intent]
            return random.choice(templates)
        
        return None


class LocalTaskExecutor:
    """本地任务执行器 - 不调用 LLM"""
    
    def __init__(self):
        self.tools = {}  # 工具注册表
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        # 系统工具
        self.register_tool("git_status", self._git_status)
        self.register_tool("git_log", self._git_log)
        self.register_tool("list_files", self._list_files)
        self.register_tool("read_file", self._read_file)
        self.register_tool("system_info", self._system_info)
    
    def register_tool(self, name: str, handler: Callable):
        """注册工具"""
        self.tools[name] = handler
    
    def _git_status(self, args: Dict = None) -> str:
        """执行 git status"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'status', '-s'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd='/workspace/projects'
            )
            if result.stdout.strip():
                return f"📋 Git 状态:\n{result.stdout}"
            return "✅ 工作区干净"
        except Exception as e:
            return f"❌ 错误: {e}"
    
    def _git_log(self, args: Dict = None) -> str:
        """执行 git log"""
        import subprocess
        try:
            n = args.get('n', 5) if args else 5
            result = subprocess.run(
                ['git', 'log', f'-{n}', '--oneline'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd='/workspace/projects'
            )
            return f"📜 最近 {n} 次提交:\n{result.stdout}"
        except Exception as e:
            return f"❌ 错误: {e}"
    
    def _list_files(self, args: Dict = None) -> str:
        """列出文件"""
        import os
        try:
            path = args.get('path', '.') if args else '.'
            full_path = os.path.join('/workspace/projects', path)
            files = os.listdir(full_path)
            return f"📁 文件列表 ({path}):\n" + "\n".join(files[:20])
        except Exception as e:
            return f"❌ 错误: {e}"
    
    def _read_file(self, args: Dict = None) -> str:
        """读取文件"""
        try:
            filepath = args.get('file') if args else None
            if not filepath:
                return "❌ 请指定文件路径"
            
            full_path = f'/workspace/projects/{filepath}'
            with open(full_path, 'r') as f:
                content = f.read()
            # 截断长文件
            if len(content) > 2000:
                content = content[:2000] + "\n... (已截断)"
            return f"📄 {filepath}:\n```\n{content}\n```"
        except Exception as e:
            return f"❌ 错误: {e}"
    
    def _system_info(self, args: Dict = None) -> str:
        """系统信息"""
        import psutil
        import os
        
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return f"""📊 系统状态:
• CPU: {cpu}%
• 内存: {mem.percent}% ({mem.used // (1024**3)}G / {mem.total // (1024**3)}G)
• 磁盘: {disk.percent}% ({disk.used // (1024**3)}G / {disk.total // (1024**3)}G)
• Python: {os.sys.version.split()[0]}"""
    
    def execute(self, intent: str, args: Dict = None) -> ExecutionResult:
        """执行本地任务"""
        start = time.time()
        
        # 映射意图到工具
        tool_map = {
            "git_status": "git_status",
            "git_log": "git_log",
            "list_files": "list_files",
            "read_file": "read_file",
            "system_info": "system_info",
        }
        
        tool_name = tool_map.get(intent)
        if tool_name and tool_name in self.tools:
            try:
                content = self.tools[tool_name](args)
                duration = (time.time() - start) * 1000
                
                return ExecutionResult(
                    success=True,
                    content=content,
                    mode_used=ExecutionMode.LOCAL_ONLY,
                    llm_calls=0,
                    brain_calls=1,
                    duration_ms=duration,
                    cached=False
                )
            except Exception as e:
                return ExecutionResult(
                    success=False,
                    content=f"执行失败: {e}",
                    mode_used=ExecutionMode.LOCAL_ONLY,
                    llm_calls=0,
                    brain_calls=1,
                    duration_ms=(time.time() - start) * 1000,
                    cached=False
                )
        
        return ExecutionResult(
            success=False,
            content="未知本地任务",
            mode_used=ExecutionMode.LOCAL_ONLY,
            llm_calls=0,
            brain_calls=0,
            duration_ms=(time.time() - start) * 1000,
            cached=False
        )


class SmartTaskExecutor:
    """
    智能任务执行器
    
    核心逻辑：
    1. 意图识别 → 决定处理方式
    2. 简单任务 → Brain 本地处理
    3. 复杂任务 → 调用 LLM
    4. 缓存结果 → 避免重复计算
    5. 学习优化 → 持续改进决策
    """
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.template_responder = TemplateResponder()
        self.local_executor = LocalTaskExecutor()
        
        # 执行统计
        self.stats = {
            "total_tasks": 0,
            "local_tasks": 0,
            "llm_tasks": 0,
            "cached_tasks": 0,
            "total_llm_calls": 0,
            "total_brain_calls": 0,
        }
        
        # 结果缓存
        self._cache: Dict[str, ExecutionResult] = {}
        self._cache_max_size = 100
    
    def _generate_cache_key(self, goal: str) -> str:
        """生成缓存键"""
        return hashlib.md5(goal.encode()).hexdigest()[:16]
    
    def _get_from_cache(self, cache_key: str) -> Optional[ExecutionResult]:
        """从缓存获取结果"""
        return self._cache.get(cache_key)
    
    def _save_to_cache(self, cache_key: str, result: ExecutionResult):
        """保存结果到缓存"""
        if len(self._cache) >= self._cache_max_size:
            # LRU: 移除最早的
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[cache_key] = result
    
    def execute(self, goal: str, use_cache: bool = True) -> ExecutionResult:
        """
        执行任务
        
        Args:
            goal: 任务目标
            use_cache: 是否使用缓存
        
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        cache_key = self._generate_cache_key(goal)
        
        # 1. 检查缓存
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                cached.cached = True
                self.stats["cached_tasks"] += 1
                logger.info(f"💾 缓存命中: {goal[:50]}...")
                return cached
        
        # 2. 意图识别
        intent, complexity, handler = self.intent_classifier.classify(goal)
        logger.info(f"🎯 意图识别: {intent}, 复杂度: {complexity}, 处理器: {handler}")
        
        # 3. 根据复杂度选择处理方式
        if handler == "template":
            # 模板响应
            response = self.template_responder.respond(intent)
            if response:
                result = ExecutionResult(
                    success=True,
                    content=response,
                    mode_used=ExecutionMode.LOCAL_ONLY,
                    llm_calls=0,
                    brain_calls=1,
                    duration_ms=(time.time() - start_time) * 1000,
                    cached=False
                )
                self._save_to_cache(cache_key, result)
                self._update_stats(result)
                return result
        
        elif handler == "local":
            # 本地执行
            result = self.local_executor.execute(intent, {"goal": goal})
            self._save_to_cache(cache_key, result)
            self._update_stats(result)
            return result
        
        elif handler == "hybrid":
            # 混合模式 - Brain 规划 + LLM 执行
            # 这里简化处理，实际应该更复杂
            result = self._execute_hybrid(goal, intent)
            self._update_stats(result)
            return result
        
        else:  # handler == "llm"
            # LLM 处理
            result = self._execute_with_llm(goal)
            self._update_stats(result)
            return result
    
    def _execute_hybrid(self, goal: str, intent: str) -> ExecutionResult:
        """混合模式执行"""
        start = time.time()
        
        # 简化：先尝试本地，失败转 LLM
        local_result = self.local_executor.execute(intent, {"goal": goal})
        
        if local_result.success:
            local_result.mode_used = ExecutionMode.HYBRID
            return local_result
        
        # 本地失败，使用 LLM
        return self._execute_with_llm(goal)
    
    def _execute_with_llm(self, goal: str) -> ExecutionResult:
        """使用 LLM 执行"""
        start = time.time()
        
        # 这里应该调用实际的 LLM
        # 简化模拟
        time.sleep(0.5)  # 模拟 LLM 延迟
        
        return ExecutionResult(
            success=True,
            content=f"[LLM 处理结果] {goal[:50]}...",
            mode_used=ExecutionMode.LLM_FIRST,
            llm_calls=1,
            brain_calls=0,
            duration_ms=(time.time() - start) * 1000,
            cached=False
        )
    
    def _update_stats(self, result: ExecutionResult):
        """更新统计"""
        self.stats["total_tasks"] += 1
        
        if result.mode_used == ExecutionMode.LOCAL_ONLY:
            self.stats["local_tasks"] += 1
        else:
            self.stats["llm_tasks"] += 1
        
        self.stats["total_llm_calls"] += result.llm_calls
        self.stats["total_brain_calls"] += result.brain_calls
    
    def get_stats_report(self) -> str:
        """获取统计报告"""
        total = self.stats["total_tasks"]
        if total == 0:
            return "暂无执行记录"
        
        local_ratio = self.stats["local_tasks"] / total * 100
        cache_ratio = self.stats["cached_tasks"] / total * 100
        
        lines = [
            "=" * 50,
            "📊 智能执行器统计",
            "=" * 50,
            f"总任务数: {total}",
            f"本地处理: {self.stats['local_tasks']} ({local_ratio:.1f}%)",
            f"LLM 处理: {self.stats['llm_tasks']} ({100-local_ratio:.1f}%)",
            f"缓存命中: {self.stats['cached_tasks']} ({cache_ratio:.1f}%)",
            f"总 LLM 调用: {self.stats['total_llm_calls']}",
            f"总 Brain 调用: {self.stats['total_brain_calls']}",
            f"效率提升: {local_ratio:.1f}%",
            "=" * 50,
        ]
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 智能任务执行优化器测试")
    print("=" * 60)
    
    executor = SmartTaskExecutor()
    
    # 测试用例
    test_cases = [
        # 简单任务 - 应该本地处理
        "查看 git 状态",
        "hi",
        "帮助",
        "列出当前目录文件",
        
        # 中等任务 - 混合处理
        "review 这段代码",
        "测试这个函数",
        
        # 复杂任务 - 需要 LLM
        "帮我重构这段代码",
        "设计一个用户认证系统",
        "实现一个登录功能",
    ]
    
    print("\n📝 执行任务测试:\n")
    
    for i, goal in enumerate(test_cases, 1):
        print(f"\n[{i}] 任务: {goal}")
        result = executor.execute(goal)
        
        mode_emoji = {
            ExecutionMode.LOCAL_ONLY: "🧠",
            ExecutionMode.HYBRID: "⚡",
            ExecutionMode.LLM_FIRST: "🤖",
        }.get(result.mode_used, "❓")
        
        print(f"    模式: {mode_emoji} {result.mode_used.value}")
        print(f"    LLM调用: {result.llm_calls}, Brain调用: {result.brain_calls}")
        print(f"    耗时: {result.duration_ms:.0f}ms")
        print(f"    结果: {result.content[:80]}...")
    
    # 再次执行测试缓存
    print("\n" + "-" * 60)
    print("🔄 缓存测试（重复执行）:")
    print("-" * 60)
    
    result1 = executor.execute("查看 git 状态")
    result2 = executor.execute("查看 git 状态")
    
    print(f"首次执行: 缓存={result1.cached}, 耗时={result1.duration_ms:.0f}ms")
    print(f"二次执行: 缓存={result2.cached}, 耗时={result2.duration_ms:.0f}ms")
    
    # 统计报告
    print("\n" + executor.get_stats_report())
    
    print("\n✅ 测试完成!")
