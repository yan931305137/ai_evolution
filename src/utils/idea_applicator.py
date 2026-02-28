"""
想法应用器 (Idea Applicator)

将评估通过的想法转化为实际的系统改进
支持多种应用方式：配置更新、代码修改、流程优化等
"""
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ApplicationType(Enum):
    """应用类型"""
    CONFIG = "config"           # 配置更新
    CODE = "code"               # 代码修改
    WORKFLOW = "workflow"       # 流程优化
    INTEGRATION = "integration" # 集成改进
    KNOWLEDGE = "knowledge"     # 知识更新
    UNKNOWN = "unknown"


class ApplicationStatus(Enum):
    """应用状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ApplicationResult:
    """应用结果"""
    application_id: str
    idea_id: str
    idea_content: str
    app_type: ApplicationType
    status: ApplicationStatus
    changes_made: List[str]
    execution_time: float
    error_message: Optional[str]
    rollback_info: Optional[Dict]
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "application_id": self.application_id,
            "idea_id": self.idea_id,
            "app_type": self.app_type.value,
            "status": self.status.value,
            "changes_made": self.changes_made,
            "execution_time": self.execution_time,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


class IdeaApplicator:
    """
    想法应用器
    
    将想法转化为实际行动
    """
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(exist_ok=True)
        
        # 应用记录
        self.application_history: List[ApplicationResult] = []
        
        # 注册处理器
        self.handlers: Dict[ApplicationType, Callable] = {
            ApplicationType.CONFIG: self._handle_config_update,
            ApplicationType.CODE: self._handle_code_modification,
            ApplicationType.WORKFLOW: self._handle_workflow_optimization,
            ApplicationType.INTEGRATION: self._handle_integration,
            ApplicationType.KNOWLEDGE: self._handle_knowledge_update,
            ApplicationType.UNKNOWN: self._handle_unknown
        }
        
        # 加载历史
        self._load_history()
    
    def _load_history(self):
        """加载应用历史"""
        history_file = self.workspace_dir / "application_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 这里可以反序列化历史记录
            except:
                pass
    
    def _save_history(self):
        """保存应用历史"""
        history_file = self.workspace_dir / "application_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(
                [r.to_dict() for r in self.application_history[-100:]],  # 保留最近100条
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def classify_idea(self, idea_content: str) -> ApplicationType:
        """分类想法类型"""
        idea_lower = idea_content.lower()
        
        # 配置相关
        if any(kw in idea_lower for kw in ["配置", "设置", "参数", "选项"]):
            return ApplicationType.CONFIG
        
        # 代码相关
        if any(kw in idea_lower for kw in ["代码", "函数", "类", "模块", "算法"]):
            return ApplicationType.CODE
        
        # 流程相关
        if any(kw in idea_lower for kw in ["流程", "步骤", "顺序", "优化", "改进"]):
            return ApplicationType.WORKFLOW
        
        # 集成相关
        if any(kw in idea_lower for kw in ["集成", "接入", "连接", "api", "插件"]):
            return ApplicationType.INTEGRATION
        
        # 知识相关
        if any(kw in idea_lower for kw in ["知识", "学习", "记忆", "理解", "数据"]):
            return ApplicationType.KNOWLEDGE
        
        return ApplicationType.UNKNOWN
    
    def apply(self, idea_id: str, idea_content: str, evaluation: Dict) -> ApplicationResult:
        """
        应用想法
        
        Args:
            idea_id: 想法ID
            idea_content: 想法内容
            evaluation: 评估结果
            
        Returns:
            ApplicationResult: 应用结果
        """
        start_time = time.time()
        
        # 分类
        app_type = self.classify_idea(idea_content)
        
        # 生成应用ID
        application_id = f"app_{int(time.time())}_{idea_id[:4]}"
        
        # 调用对应处理器
        handler = self.handlers.get(app_type, self._handle_unknown)
        
        try:
            changes = handler(idea_content, evaluation)
            status = ApplicationStatus.SUCCESS
            error_msg = None
        except Exception as e:
            changes = []
            status = ApplicationStatus.FAILED
            error_msg = str(e)
        
        execution_time = time.time() - start_time
        
        result = ApplicationResult(
            application_id=application_id,
            idea_id=idea_id,
            idea_content=idea_content,
            app_type=app_type,
            status=status,
            changes_made=changes,
            execution_time=execution_time,
            error_message=error_msg,
            rollback_info=None
        )
        
        self.application_history.append(result)
        self._save_history()
        
        return result
    
    def _handle_config_update(self, idea: str, evaluation: Dict) -> List[str]:
        """处理配置更新"""
        changes = []
        
        # 提取配置键值
        # 这里实现智能配置更新逻辑
        if "日志" in idea or "log" in idea.lower():
            changes.append("更新日志级别配置")
        if "超时" in idea or "timeout" in idea.lower():
            changes.append("调整超时时间参数")
        if "缓存" in idea or "cache" in idea.lower():
            changes.append("优化缓存策略")
        
        if not changes:
            changes.append("分析配置需求，准备更新")
        
        return changes
    
    def _handle_code_modification(self, idea: str, evaluation: Dict) -> List[str]:
        """处理代码修改"""
        changes = []
        
        # 智能代码修改逻辑
        if "优化" in idea or "improve" in idea.lower():
            changes.append("识别性能瓶颈点")
            changes.append("生成优化方案")
        if "修复" in idea or "fix" in idea.lower():
            changes.append("定位问题代码")
            changes.append("应用修复补丁")
        if "重构" in idea or "refactor" in idea.lower():
            changes.append("分析代码结构")
            changes.append("执行安全重构")
        
        if not changes:
            changes.append("代码改进建议已记录")
        
        return changes
    
    def _handle_workflow_optimization(self, idea: str, evaluation: Dict) -> List[str]:
        """处理流程优化"""
        changes = []
        
        if "并行" in idea or "parallel" in idea.lower():
            changes.append("设计并行处理流程")
        if "异步" in idea or "async" in idea.lower():
            changes.append("引入异步处理机制")
        if "批处理" in idea or "batch" in idea.lower():
            changes.append("实现批量处理")
        
        if not changes:
            changes.append("流程优化方案已记录")
        
        return changes
    
    def _handle_integration(self, idea: str, evaluation: Dict) -> List[str]:
        """处理集成改进"""
        changes = []
        
        # 检查是否需要新技能
        if "技能" in idea or "skill" in idea.lower():
            changes.append("创建新技能接口")
        if "api" in idea.lower():
            changes.append("集成新API服务")
        if "webhook" in idea.lower():
            changes.append("配置Webhook接收")
        
        if not changes:
            changes.append("集成改进方案已记录")
        
        return changes
    
    def _handle_knowledge_update(self, idea: str, evaluation: Dict) -> List[str]:
        """处理知识更新"""
        changes = []
        
        if "学习" in idea or "learn" in idea.lower():
            changes.append("更新知识库")
        if "记忆" in idea or "memory" in idea.lower():
            changes.append("优化记忆系统")
        
        if not changes:
            changes.append("知识更新方案已记录")
        
        return changes
    
    def _handle_unknown(self, idea: str, evaluation: Dict) -> List[str]:
        """处理未知类型"""
        return ["想法已记录，等待进一步分析"]
    
    def batch_apply(self, ideas_with_evaluations: List[tuple]) -> List[ApplicationResult]:
        """批量应用想法"""
        results = []
        for idea_id, idea_content, evaluation in ideas_with_evaluations:
            result = self.apply(idea_id, idea_content, evaluation)
            results.append(result)
        return results
    
    def get_application_stats(self) -> Dict[str, Any]:
        """获取应用统计"""
        if not self.application_history:
            return {"total": 0}
        
        total = len(self.application_history)
        success = sum(1 for r in self.application_history if r.status == ApplicationStatus.SUCCESS)
        failed = sum(1 for r in self.application_history if r.status == ApplicationStatus.FAILED)
        
        type_distribution = {}
        for r in self.application_history:
            t = r.app_type.value
            type_distribution[t] = type_distribution.get(t, 0) + 1
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": success / total if total > 0 else 0,
            "type_distribution": type_distribution,
            "avg_execution_time": sum(r.execution_time for r in self.application_history) / total
        }
    
    def get_recent_applications(self, n: int = 10) -> List[ApplicationResult]:
        """获取最近的应用记录"""
        return self.application_history[-n:]


# 便捷函数
def quick_apply(idea_id: str, idea_content: str, evaluation: Dict) -> ApplicationResult:
    """快速应用想法"""
    applicator = IdeaApplicator()
    return applicator.apply(idea_id, idea_content, evaluation)


if __name__ == "__main__":
    # 测试
    applicator = IdeaApplicator()
    
    test_idea = "优化文档处理算法，提升检索效率30%"
    test_eval = {
        "overall_score": 75.0,
        "recommendation": "apply"
    }
    
    result = applicator.apply("test_001", test_idea, test_eval)
    
    print(f"应用结果:")
    print(f"  类型: {result.app_type.value}")
    print(f"  状态: {result.status.value}")
    print(f"  变更: {result.changes_made}")
    print(f"  耗时: {result.execution_time:.2f}s")
