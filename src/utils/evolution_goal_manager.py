"""
进化目标配置系统 (Evolution Goal Configuration System)

允许用户配置AI的进化方向和目标，实现：
1. 可配置的进化维度（能力、知识、效率等）
2. 目标权重设置
3. 进化策略选择
4. 评估标准定义
"""
import json
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EvolutionDimension(Enum):
    """进化维度"""
    CAPABILITY = "capability"      # 能力提升
    KNOWLEDGE = "knowledge"        # 知识积累
    EFFICIENCY = "efficiency"      # 效率优化
    CREATIVITY = "creativity"      # 创造力增强
    SOCIAL = "social"              # 社交能力
    ADAPTATION = "adaptation"      # 适应能力


class EvolutionStrategy(Enum):
    """进化策略"""
    EXPLORATION = "exploration"    # 探索优先
    EXPLOITATION = "exploitation"  # 利用优先
    BALANCED = "balanced"          # 平衡策略
    FOCUSED = "focused"            # 专注策略


@dataclass
class EvolutionGoal:
    """进化目标"""
    name: str
    dimension: EvolutionDimension
    description: str
    target_value: float  # 目标值 0-100
    current_value: float = 0.0  # 当前值
    weight: float = 1.0  # 权重
    priority: int = 1  # 优先级 1-5
    metrics: List[str] = field(default_factory=list)  # 评估指标
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "dimension": self.dimension.value,
            "description": self.description,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "weight": self.weight,
            "priority": self.priority,
            "metrics": self.metrics,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EvolutionGoal":
        return cls(
            name=data["name"],
            dimension=EvolutionDimension(data["dimension"]),
            description=data["description"],
            target_value=data["target_value"],
            current_value=data.get("current_value", 0.0),
            weight=data.get("weight", 1.0),
            priority=data.get("priority", 1),
            metrics=data.get("metrics", []),
            enabled=data.get("enabled", True)
        )


@dataclass
class IdeaApplication:
    """想法应用记录"""
    idea_id: str
    idea_content: str
    applied_at: float
    success_score: float  # 0-100
    feedback: str
    evolution_impact: Dict[str, float]  # 对各维度的影响


class EvolutionGoalManager:
    """
    进化目标管理器
    
    管理进化目标、评估想法、应用改进
    """
    
    DEFAULT_CONFIG_PATH = "config/evolution_goals.yaml"
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self.goals: Dict[str, EvolutionGoal] = {}
        self.strategy: EvolutionStrategy = EvolutionStrategy.BALANCED
        self.idea_applications: List[IdeaApplication] = []
        self.evolution_history: List[Dict] = []
        
        # 加载或创建默认配置
        self._load_or_create_config()
    
    def _load_or_create_config(self):
        """加载或创建默认配置"""
        if self.config_path.exists():
            self._load_config()
        else:
            self._create_default_config()
    
    def _load_config(self):
        """从YAML加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 加载策略
            self.strategy = EvolutionStrategy(config.get("strategy", "balanced"))
            
            # 加载目标
            for goal_data in config.get("goals", []):
                goal = EvolutionGoal.from_dict(goal_data)
                self.goals[goal.name] = goal
                
            print(f"✅ 已加载 {len(self.goals)} 个进化目标")
            
        except Exception as e:
            print(f"⚠️  加载配置失败: {e}，使用默认配置")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self.strategy = EvolutionStrategy.BALANCED
        
        # 默认目标
        default_goals = [
            EvolutionGoal(
                name="能力提升",
                dimension=EvolutionDimension.CAPABILITY,
                description="提升核心能力，包括推理、学习、创造等",
                target_value=90.0,
                weight=1.5,
                priority=1,
                metrics=["任务成功率", "学习速度", "错误率"]
            ),
            EvolutionGoal(
                name="知识积累",
                dimension=EvolutionDimension.KNOWLEDGE,
                description="扩展知识面和深度",
                target_value=85.0,
                weight=1.2,
                priority=2,
                metrics=["知识覆盖率", "知识准确率", "检索效率"]
            ),
            EvolutionGoal(
                name="效率优化",
                dimension=EvolutionDimension.EFFICIENCY,
                description="提高处理速度和资源利用率",
                target_value=80.0,
                weight=1.0,
                priority=3,
                metrics=["响应时间", "资源消耗", "吞吐量"]
            ),
            EvolutionGoal(
                name="创造力增强",
                dimension=EvolutionDimension.CREATIVITY,
                description="提升创新思维和问题解决能力",
                target_value=75.0,
                weight=1.0,
                priority=3,
                metrics=["创意质量", "多样性", "可行性"]
            ),
        ]
        
        for goal in default_goals:
            self.goals[goal.name] = goal
        
        # 保存默认配置
        self.save_config()
        print(f"✅ 已创建默认配置，{len(self.goals)} 个进化目标")
    
    def save_config(self):
        """保存配置到YAML"""
        config = {
            "strategy": self.strategy.value,
            "goals": [goal.to_dict() for goal in self.goals.values()]
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    def add_goal(self, goal: EvolutionGoal):
        """添加新目标"""
        self.goals[goal.name] = goal
        self.save_config()
    
    def remove_goal(self, name: str):
        """移除目标"""
        if name in self.goals:
            del self.goals[name]
            self.save_config()
    
    def get_active_goals(self) -> List[EvolutionGoal]:
        """获取启用的目标，按优先级排序"""
        return sorted(
            [g for g in self.goals.values() if g.enabled],
            key=lambda x: (x.priority, -x.weight)
        )
    
    def evaluate_idea(self, idea_content: str, idea_method: str) -> Dict[str, Any]:
        """
        评估想法对进化目标的贡献
        
        Returns:
            {
                "overall_score": float,  # 0-100
                "dimension_scores": Dict[str, float],  # 各维度得分
                "best_match_goal": str,  # 最匹配的目标
                "recommendation": str  # 建议
            }
        """
        # 基于关键词匹配评估
        dimension_scores = {dim.value: 0.0 for dim in EvolutionDimension}
        
        # 关键词映射
        keyword_mapping = {
            EvolutionDimension.CAPABILITY: ["能力", "性能", "优化", "提升", "改进", "算法", "推理", "学习"],
            EvolutionDimension.KNOWLEDGE: ["知识", "数据", "信息", "学习", "记忆", "理解"],
            EvolutionDimension.EFFICIENCY: ["效率", "速度", "性能", "资源", "时间", "快速"],
            EvolutionDimension.CREATIVITY: ["创意", "创新", "想法", "设计", "新颖", "独特"],
            EvolutionDimension.SOCIAL: ["交互", "沟通", "协作", "用户", "社交", "对话"],
            EvolutionDimension.ADAPTATION: ["适应", "调整", "变化", "灵活", "动态"]
        }
        
        idea_lower = idea_content.lower()
        
        for dim, keywords in keyword_mapping.items():
            score = sum(10 for kw in keywords if kw in idea_lower)
            dimension_scores[dim.value] = min(100, score)
        
        # 计算加权总分
        total_weight = 0
        weighted_score = 0
        best_match = None
        best_score = 0
        
        for goal in self.get_active_goals():
            dim_score = dimension_scores.get(goal.dimension.value, 0)
            weighted = dim_score * goal.weight
            weighted_score += weighted
            total_weight += goal.weight
            
            if dim_score > best_score:
                best_score = dim_score
                best_match = goal.name
        
        overall_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # 生成建议
        if overall_score >= 70:
            recommendation = "强烈建议应用这个想法"
        elif overall_score >= 50:
            recommendation = "可以考虑应用，建议进一步评估"
        else:
            recommendation = "与当前进化目标匹配度较低"
        
        return {
            "overall_score": overall_score,
            "dimension_scores": dimension_scores,
            "best_match_goal": best_match or "无",
            "recommendation": recommendation
        }
    
    def apply_idea(self, idea_content: str, evaluation: Dict) -> IdeaApplication:
        """
        应用想法并记录
        
        这会将想法转化为实际的系统改进
        """
        import time
        
        # 模拟应用过程（实际实现中可以调用具体的优化工具）
        application = IdeaApplication(
            idea_id=f"idea_{int(time.time())}",
            idea_content=idea_content,
            applied_at=time.time(),
            success_score=evaluation["overall_score"],
            feedback="已应用想法",
            evolution_impact=evaluation["dimension_scores"]
        )
        
        self.idea_applications.append(application)
        
        # 更新进化历史
        self.evolution_history.append({
            "timestamp": application.applied_at,
            "idea": idea_content[:100],
            "score": application.success_score,
            "impact": application.evolution_impact
        })
        
        return application
    
    def get_evolution_progress(self) -> Dict:
        """获取进化进度"""
        total_goals = len(self.goals)
        active_goals = len(self.get_active_goals())
        
        # 计算总体进度
        if self.goals:
            avg_progress = sum(
                g.current_value / g.target_value * 100 
                for g in self.goals.values()
            ) / len(self.goals)
        else:
            avg_progress = 0
        
        return {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "overall_progress": avg_progress,
            "applied_ideas": len(self.idea_applications),
            "strategy": self.strategy.value,
            "goal_details": {
                name: {
                    "current": g.current_value,
                    "target": g.target_value,
                    "progress": g.current_value / g.target_value * 100
                }
                for name, g in self.goals.items()
            }
        }
    
    def update_goal_progress(self, goal_name: str, new_value: float):
        """更新目标进度"""
        if goal_name in self.goals:
            self.goals[goal_name].current_value = min(
                new_value, 
                self.goals[goal_name].target_value
            )
            self.save_config()
    
    def print_config(self):
        """打印当前配置"""
        print("\n" + "="*60)
        print("🎯 进化目标配置")
        print("="*60)
        print(f"策略: {self.strategy.value}")
        print(f"目标数量: {len(self.goals)}")
        print("\n目标列表:")
        
        for name, goal in sorted(self.goals.items(), key=lambda x: x[1].priority):
            status = "✅" if goal.enabled else "❌"
            progress = goal.current_value / goal.target_value * 100
            print(f"  {status} [{goal.priority}] {name}")
            print(f"     维度: {goal.dimension.value}")
            print(f"     进度: {goal.current_value:.1f}/{goal.target_value:.1f} ({progress:.1f}%)")
            print(f"     权重: {goal.weight}")
            print()


# 便捷函数
def create_default_evolution_config():
    """创建默认进化配置"""
    manager = EvolutionGoalManager()
    manager.print_config()
    return manager


if __name__ == "__main__":
    # 测试
    manager = create_default_evolution_config()
    
    # 测试想法评估
    test_idea = "优化文档处理算法，提升检索效率30%"
    result = manager.evaluate_idea(test_idea, "combinatorial")
    print(f"\n想法评估: {test_idea}")
    print(f"总分: {result['overall_score']:.1f}")
    print(f"最匹配目标: {result['best_match_goal']}")
    print(f"建议: {result['recommendation']}")
