"""
任务数据工厂

生成各种测试用的任务数据
"""

import random
from typing import List, Dict, Any, Optional
from enum import Enum


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskFactory:
    """任务数据工厂"""
    
    TASK_TEMPLATES = [
        {"name": "代码审查", "category": "development", "duration": 30},
        {"name": "编写文档", "category": "documentation", "duration": 60},
        {"name": "修复Bug", "category": "development", "duration": 45},
        {"name": "代码重构", "category": "development", "duration": 120},
        {"name": "编写测试", "category": "testing", "duration": 90},
        {"name": "性能优化", "category": "optimization", "duration": 180},
        {"name": "学习新技术", "category": "learning", "duration": 240},
        {"name": "会议讨论", "category": "communication", "duration": 60},
        {"name": "部署应用", "category": "devops", "duration": 30},
        {"name": "数据分析", "category": "analysis", "duration": 90},
    ]
    
    @classmethod
    def create_task(
        cls,
        name: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        status: TaskStatus = TaskStatus.PENDING,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建单个任务
        
        Args:
            name: 任务名称
            category: 任务类别
            priority: 优先级
            status: 状态
            **kwargs: 其他属性
        
        Returns:
            任务数据字典
        """
        template = random.choice(cls.TASK_TEMPLATES) if not name else None
        
        return {
            "id": kwargs.get('id', f"task_{random.randint(1000, 9999)}"),
            "name": name or template["name"],
            "description": kwargs.get('description', f"执行{name or template['name']}任务"),
            "category": category or (template["category"] if template else "general"),
            "priority": (priority or TaskPriority.MEDIUM).value,
            "priority_label": (priority or TaskPriority.MEDIUM).name,
            "status": status.value,
            "estimated_duration": kwargs.get('duration', template["duration"] if template else 60),
            "dependencies": kwargs.get('dependencies', []),
            "resources_required": kwargs.get('resources', []),
            "metadata": {
                "creator": kwargs.get('creator', 'test'),
                "created_at": kwargs.get('created_at', '2024-01-01T00:00:00'),
                "tags": kwargs.get('tags', []),
            }
        }
    
    @classmethod
    def create_task_chain(
        cls,
        length: int = 5,
        base_name: str = "步骤",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        创建任务链（有依赖关系的任务序列）
        
        Args:
            length: 任务数量
            base_name: 任务名称前缀
            **kwargs: 其他参数
        
        Returns:
            任务列表，每个任务依赖前一个
        """
        tasks = []
        prev_id = None
        
        for i in range(length):
            task_id = f"chain_task_{i}"
            task = cls.create_task(
                id=task_id,
                name=f"{base_name} {i+1}",
                priority=kwargs.get('priority', TaskPriority.MEDIUM),
                dependencies=[prev_id] if prev_id else [],
                **kwargs
            )
            tasks.append(task)
            prev_id = task_id
        
        return tasks
    
    @classmethod
    def create_parallel_tasks(
        cls,
        count: int = 3,
        base_name: str = "并行任务",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        创建并行任务（无依赖关系）
        
        Args:
            count: 任务数量
            base_name: 任务名称前缀
            **kwargs: 其他参数
        
        Returns:
            任务列表
        """
        return [
            cls.create_task(
                id=f"parallel_task_{i}",
                name=f"{base_name} {i+1}",
                dependencies=[],
                **kwargs
            )
            for i in range(count)
        ]
    
    @classmethod
    def create_complex_workflow(
        cls,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        创建复杂工作流（混合并行和串行）
        
        结构示例:
            A
           / \
          B   C
          |   |
          D   E
           \ /
            F
        
        Returns:
            任务列表
        """
        tasks = []
        
        # 起始任务
        task_a = cls.create_task(id="A", name="初始化", dependencies=[])
        tasks.append(task_a)
        
        # 并行层
        task_b = cls.create_task(id="B", name="处理分支1", dependencies=["A"])
        task_c = cls.create_task(id="C", name="处理分支2", dependencies=["A"])
        tasks.extend([task_b, task_c])
        
        # 下一层并行
        task_d = cls.create_task(id="D", name="子处理1", dependencies=["B"])
        task_e = cls.create_task(id="E", name="子处理2", dependencies=["C"])
        tasks.extend([task_d, task_e])
        
        # 合并任务
        task_f = cls.create_task(id="F", name="汇总结果", dependencies=["D", "E"])
        tasks.append(task_f)
        
        return tasks
    
    @classmethod
    def create_batch(
        cls,
        count: int = 10,
        priority_distribution: Optional[Dict[TaskPriority, float]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量创建任务
        
        Args:
            count: 任务数量
            priority_distribution: 优先级分布 {优先级: 比例}
            **kwargs: 其他参数
        
        Returns:
            任务列表
        """
        if priority_distribution is None:
            priority_distribution = {
                TaskPriority.LOW: 0.2,
                TaskPriority.MEDIUM: 0.4,
                TaskPriority.HIGH: 0.3,
                TaskPriority.CRITICAL: 0.1
            }
        
        tasks = []
        priorities = list(priority_distribution.keys())
        weights = list(priority_distribution.values())
        
        for i in range(count):
            priority = random.choices(priorities, weights=weights)[0]
            task = cls.create_task(
                id=f"batch_task_{i}",
                priority=priority,
                **kwargs
            )
            tasks.append(task)
        
        return tasks
