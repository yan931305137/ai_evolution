"""
Self-Evolution System - 真正的自我进化系统

实现AI的自我改进能力：
1. 自我评估与反思
2. 策略学习与优化
3. 失败经验学习
4. 代码自我改进（谨慎）
5. 元学习（学习如何学习）
"""
import json
import re
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import asyncio


class ImprovementType(Enum):
    """改进类型"""
    STRATEGY = "strategy"          # 策略改进
    PROMPT = "prompt"              # 提示词优化
    PARAMETER = "parameter"        # 参数调整
    KNOWLEDGE = "knowledge"        # 知识更新
    SKILL = "skill"                # 技能学习
    META = "meta"                  # 元能力改进


class EvolutionStatus(Enum):
    """进化状态"""
    PROPOSED = "proposed"          # 已提议
    TESTING = "testing"            # 测试中
    VALIDATED = "validated"        # 已验证
    REJECTED = "rejected"          # 已拒绝
    DEPLOYED = "deployed"          # 已部署
    ROLLED_BACK = "rolled_back"    # 已回滚


@dataclass
class Experience:
    """经验样本"""
    situation: str                  # 情境描述
    action: str                     # 采取的行动
    outcome: str                    # 结果
    reward: float                   # 奖励/惩罚 (-1 到 1)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "situation": self.situation,
            "action": self.action,
            "outcome": self.outcome,
            "reward": self.reward,
            "context": self.context,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ImprovementProposal:
    """改进提案"""
    id: str
    improvement_type: ImprovementType
    description: str                # 改进描述
    rationale: str                  # 改进理由
    target_component: str           # 目标组件
    proposed_change: Dict           # 提议的更改
    expected_benefit: float         # 预期收益
    risk_level: float               # 风险等级 0-1
    
    status: EvolutionStatus = EvolutionStatus.PROPOSED
    test_results: List[Dict] = field(default_factory=list)
    validation_score: Optional[float] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    tested_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.improvement_type.value,
            "description": self.description,
            "rationale": self.rationale,
            "target_component": self.target_component,
            "proposed_change": self.proposed_change,
            "expected_benefit": self.expected_benefit,
            "risk_level": self.risk_level,
            "status": self.status.value,
            "validation_score": self.validation_score,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: datetime
    metrics: Dict[str, float]       # 性能指标
    context: Dict[str, Any]         # 上下文信息
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "context": self.context
        }


class StrategyLibrary:
    """
    策略库
    
    存储和管理不同情境下的策略
    """
    
    def __init__(self):
        self.strategies: Dict[str, List[Dict]] = defaultdict(list)  # 情境 -> 策略列表
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)
    
    def add_strategy(self, situation_type: str, strategy: Dict, initial_score: float = 0.5):
        """添加策略"""
        strategy_id = f"{situation_type}_{len(self.strategies[situation_type])}"
        strategy["id"] = strategy_id
        strategy["created_at"] = datetime.now().isoformat()
        strategy["usage_count"] = 0
        
        self.strategies[situation_type].append(strategy)
        self.strategy_performance[strategy_id] = [initial_score]
    
    def get_best_strategy(self, situation_type: str, context: Dict = None) -> Optional[Dict]:
        """获取最佳策略"""
        strategies = self.strategies.get(situation_type, [])
        if not strategies:
            return None
        
        # 计算平均表现分数
        scored_strategies = []
        for s in strategies:
            sid = s["id"]
            scores = self.strategy_performance.get(sid, [0.5])
            avg_score = sum(scores) / len(scores)
            scored_strategies.append((s, avg_score))
        
        # 按分数排序，返回最佳策略
        scored_strategies.sort(key=lambda x: x[1], reverse=True)
        best_strategy = scored_strategies[0][0]
        best_strategy["usage_count"] += 1
        
        return best_strategy
    
    def update_strategy_performance(self, strategy_id: str, outcome_score: float):
        """更新策略表现"""
        self.strategy_performance[strategy_id].append(outcome_score)
        # 只保留最近100个分数
        if len(self.strategy_performance[strategy_id]) > 100:
            self.strategy_performance[strategy_id] = self.strategy_performance[strategy_id][-100:]


class SelfEvolutionEngine:
    """
    自我进化引擎
    
    核心进化机制
    """
    
    def __init__(self, brain_reference=None):
        self.brain = brain_reference
        self.experience_buffer: List[Experience] = []
        self.proposals: List[ImprovementProposal] = []
        self.performance_history: List[PerformanceSnapshot] = []
        self.strategy_library = StrategyLibrary()
        
        # 进化参数
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.improvement_threshold = 0.1
        
        # 自我评估指标
        self.metrics = {
            "response_quality": [],
            "user_satisfaction": [],
            "task_success_rate": [],
            "learning_efficiency": []
        }
        
        # 反射日志
        self.reflection_log: List[Dict] = []
    
    def record_experience(
        self,
        situation: str,
        action: str,
        outcome: str,
        reward: float,
        context: Optional[Dict] = None
    ):
        """
        记录经验
        
        Args:
            situation: 情境
            action: 行动
            outcome: 结果
            reward: 奖励 (-1 到 1)
            context: 上下文
        """
        experience = Experience(
            situation=situation,
            action=action,
            outcome=outcome,
            reward=reward,
            context=context or {}
        )
        
        self.experience_buffer.append(experience)
        
        # 只保留最近1000条经验
        if len(self.experience_buffer) > 1000:
            self.experience_buffer = self.experience_buffer[-1000:]
        
        # 触发学习
        if len(self.experience_buffer) % 10 == 0:  # 每10条经验学习一次
            asyncio.create_task(self._learn_from_experiences())
    
    async def _learn_from_experiences(self):
        """从经验中学习"""
        if len(self.experience_buffer) < 10:
            return
        
        # 分析最近的经验
        recent_experiences = self.experience_buffer[-20:]
        
        # 1. 识别成功模式
        successful = [e for e in recent_experiences if e.reward > 0.5]
        failed = [e for e in recent_experiences if e.reward < -0.3]
        
        # 2. 更新策略库
        for exp in successful:
            self._extract_and_store_strategy(exp)
        
        # 3. 分析失败原因
        if failed:
            failure_analysis = self._analyze_failures(failed)
            await self._generate_improvement_proposals(failure_analysis)
        
        # 4. 更新性能指标
        self._update_metrics(recent_experiences)
    
    def _extract_and_store_strategy(self, experience: Experience):
        """从成功经验中提取策略"""
        situation_type = self._classify_situation(experience.situation)
        
        strategy = {
            "description": experience.action,
            "context_requirements": experience.context,
            "expected_outcome": experience.outcome
        }
        
        self.strategy_library.add_strategy(
            situation_type=situation_type,
            strategy=strategy,
            initial_score=experience.reward
        )
    
    def _classify_situation(self, situation: str) -> str:
        """分类情境"""
        # 简单的关键词分类
        keywords = {
            "coding": ["代码", "编程", "bug", "程序", "function"],
            "conversation": ["聊天", "对话", "交流", "讨论"],
            "problem_solving": ["问题", "解决", "方案", "怎么办"],
            "learning": ["学习", "了解", "知识", "教"],
            "planning": ["计划", "安排", "规划", "准备"]
        }
        
        situation_lower = situation.lower()
        for category, words in keywords.items():
            if any(w in situation_lower for w in words):
                return category
        
        return "general"
    
    def _analyze_failures(self, failed_experiences: List[Experience]) -> Dict:
        """分析失败原因"""
        analysis = {
            "count": len(failed_experiences),
            "common_patterns": [],
            "suggested_improvements": []
        }
        
        # 找出共同模式
        situations = [e.situation for e in failed_experiences]
        actions = [e.action for e in failed_experiences]
        
        # 简化的模式检测
        if len(set(actions)) < len(actions) * 0.5:
            analysis["common_patterns"].append("重复使用无效策略")
            analysis["suggested_improvements"].append("增加策略多样性")
        
        # 检查是否需要更多知识
        knowledge_indicators = ["不知道", "不清楚", "不确定"]
        if any(k in " ".join(situations) for k in knowledge_indicators):
            analysis["common_patterns"].append("知识不足")
            analysis["suggested_improvements"].append("补充领域知识")
        
        return analysis
    
    async def _generate_improvement_proposals(self, failure_analysis: Dict):
        """生成改进提案"""
        for suggestion in failure_analysis.get("suggested_improvements", []):
            proposal = self._create_proposal_from_suggestion(suggestion)
            if proposal:
                self.proposals.append(proposal)
    
    def _create_proposal_from_suggestion(self, suggestion: str) -> Optional[ImprovementProposal]:
        """根据建议创建提案"""
        import uuid
        
        if "策略" in suggestion:
            return ImprovementProposal(
                id=str(uuid.uuid4())[:8],
                improvement_type=ImprovementType.STRATEGY,
                description="增加策略多样性",
                rationale=failure_analysis="检测到重复使用无效策略",
                target_component="strategy_library",
                proposed_change={"exploration_rate": 0.3},
                expected_benefit=0.2,
                risk_level=0.1
            )
        elif "知识" in suggestion:
            return ImprovementProposal(
                id=str(uuid.uuid4())[:8],
                improvement_type=ImprovementType.KNOWLEDGE,
                description="补充领域知识",
                rationale="检测到知识缺口导致失败",
                target_component="knowledge_base",
                proposed_change={"update_trigger": "on_failure"},
                expected_benefit=0.3,
                risk_level=0.2
            )
        
        return None
    
    def _update_metrics(self, experiences: List[Experience]):
        """更新性能指标"""
        rewards = [e.reward for e in experiences]
        avg_reward = sum(rewards) / len(rewards) if rewards else 0
        
        self.metrics["response_quality"].append(avg_reward)
        if len(self.metrics["response_quality"]) > 100:
            self.metrics["response_quality"] = self.metrics["response_quality"][-100:]
    
    def reflect(self) -> Dict:
        """
        自我反思
        
        定期评估自己的表现和进步
        """
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "period": "last_24h",
            "summary": {},
            "insights": [],
            "action_items": []
        }
        
        # 1. 性能趋势分析
        for metric_name, values in self.metrics.items():
            if len(values) >= 2:
                recent = sum(values[-10:]) / min(len(values), 10)
                older = sum(values[-20:-10]) / min(max(len(values) - 10, 1), 10)
                trend = "improving" if recent > older else "declining" if recent < older else "stable"
                
                reflection["summary"][metric_name] = {
                    "current": recent,
                    "trend": trend,
                    "change": recent - older
                }
        
        # 2. 生成洞察
        if reflection["summary"].get("response_quality", {}).get("trend") == "declining":
            reflection["insights"].append("响应质量下降，可能需要调整策略")
            reflection["action_items"].append("审查最近失败的交互")
        
        # 3. 检查学习效果
        if len(self.experience_buffer) > 100:
            recent_success_rate = len([e for e in self.experience_buffer[-100:] if e.reward > 0]) / 100
            if recent_success_rate < 0.6:
                reflection["insights"].append("成功率偏低，需要改进学习方法")
                reflection["action_items"].append("增加探索率以发现新策略")
        
        self.reflection_log.append(reflection)
        return reflection
    
    def evaluate_proposal(self, proposal_id: str, test_results: Dict) -> bool:
        """
        评估改进提案
        
        Args:
            proposal_id: 提案ID
            test_results: 测试结果
            
        Returns:
            是否通过验证
        """
        proposal = next((p for p in self.proposals if p.id == proposal_id), None)
        if not proposal:
            return False
        
        proposal.test_results.append(test_results)
        
        # 计算验证分数
        if "performance_improvement" in test_results:
            improvement = test_results["performance_improvement"]
            proposal.validation_score = improvement
            
            # 决定是否接受
            if improvement > proposal.expected_benefit * 0.5:
                proposal.status = EvolutionStatus.VALIDATED
                return True
            else:
                proposal.status = EvolutionStatus.REJECTED
                return False
        
        return False
    
    def deploy_improvement(self, proposal_id: str) -> bool:
        """
        部署改进
        
        Args:
            proposal_id: 提案ID
            
        Returns:
            是否成功部署
        """
        proposal = next((p for p in self.proposals if p.id == proposal_id), None)
        if not proposal or proposal.status != EvolutionStatus.VALIDATED:
            return False
        
        # 实际部署改进
        try:
            if proposal.improvement_type == ImprovementType.STRATEGY:
                self._deploy_strategy_improvement(proposal)
            elif proposal.improvement_type == ImprovementType.PARAMETER:
                self._deploy_parameter_improvement(proposal)
            
            proposal.status = EvolutionStatus.DEPLOYED
            proposal.deployed_at = datetime.now()
            return True
            
        except Exception as e:
            print(f"部署改进失败: {e}")
            return False
    
    def _deploy_strategy_improvement(self, proposal: ImprovementProposal):
        """部署策略改进"""
        # 更新策略库参数
        change = proposal.proposed_change
        if "exploration_rate" in change:
            self.exploration_rate = change["exploration_rate"]
    
    def _deploy_parameter_improvement(self, proposal: ImprovementProposal):
        """部署参数改进"""
        change = proposal.proposed_change
        for param, value in change.items():
            if hasattr(self, param):
                setattr(self, param, value)
    
    def get_best_strategy_for(self, situation: str) -> Optional[Dict]:
        """获取情境的最佳策略"""
        situation_type = self._classify_situation(situation)
        return self.strategy_library.get_best_strategy(situation_type)
    
    def get_evolution_report(self) -> Dict:
        """获取进化报告"""
        return {
            "total_experiences": len(self.experience_buffer),
            "active_proposals": len([p for p in self.proposals if p.status in [EvolutionStatus.PROPOSED, EvolutionStatus.TESTING]]),
            "validated_improvements": len([p for p in self.proposals if p.status == EvolutionStatus.VALIDATED]),
            "deployed_improvements": len([p for p in self.proposals if p.status == EvolutionStatus.DEPLOYED]),
            "current_metrics": {
                name: sum(values[-10:]) / min(len(values), 10) if values else 0
                for name, values in self.metrics.items()
            },
            "strategy_count": sum(len(strategies) for strategies in self.strategy_library.strategies.values()),
            "recent_reflections": self.reflection_log[-5:]
        }
    
    def save_state(self, filepath: str):
        """保存进化状态"""
        state = {
            "experiences": [e.to_dict() for e in self.experience_buffer],
            "proposals": [p.to_dict() for p in self.proposals],
            "metrics": self.metrics,
            "parameters": {
                "learning_rate": self.learning_rate,
                "exploration_rate": self.exploration_rate
            },
            "reflection_log": self.reflection_log,
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load_state(self, filepath: str):
        """加载进化状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 恢复经验
            for exp_data in state.get("experiences", []):
                exp = Experience(
                    situation=exp_data["situation"],
                    action=exp_data["action"],
                    outcome=exp_data["outcome"],
                    reward=exp_data["reward"],
                    context=exp_data.get("context", {}),
                    timestamp=datetime.fromisoformat(exp_data["timestamp"])
                )
                self.experience_buffer.append(exp)
            
            # 恢复参数
            params = state.get("parameters", {})
            self.learning_rate = params.get("learning_rate", 0.1)
            self.exploration_rate = params.get("exploration_rate", 0.2)
            
            print(f"✅ 进化状态已加载：{len(self.experience_buffer)}条经验")
            
        except FileNotFoundError:
            print("⚠️ 进化状态文件不存在，从空状态开始")
        except Exception as e:
            print(f"❌ 加载进化状态失败：{e}")


class MetaLearningSystem:
    """
    元学习系统
    
    学习如何学习，优化学习策略本身
    """
    
    def __init__(self, evolution_engine: SelfEvolutionEngine):
        self.evolution = evolution_engine
        self.learning_strategies: List[Dict] = []
        self.meta_experiences: List[Dict] = []
    
    def evaluate_learning_effectiveness(self) -> Dict:
        """评估学习效果"""
        if len(self.evolution.experience_buffer) < 50:
            return {"status": "insufficient_data"}
        
        # 分析学习效率
        experiences = self.evolution.experience_buffer
        
        # 计算学习曲线
        window_size = 20
        learning_curve = []
        for i in range(0, len(experiences) - window_size, window_size):
            window = experiences[i:i+window_size]
            avg_reward = sum(e.reward for e in window) / window_size
            learning_curve.append(avg_reward)
        
        # 判断学习是否有效
        if len(learning_curve) >= 2:
            improvement = learning_curve[-1] - learning_curve[0]
            return {
                "status": "improving" if improvement > 0 else "plateau" if abs(improvement) < 0.1 else "declining",
                "total_improvement": improvement,
                "learning_curve": learning_curve,
                "recommendation": self._recommend_meta_adjustment(improvement)
            }
        
        return {"status": "collecting_data"}
    
    def _recommend_meta_adjustment(self, improvement: float) -> str:
        """推荐元调整"""
        if improvement < -0.2:
            return "考虑完全改变学习方法，当前策略无效"
        elif improvement < 0:
            return "增加探索率，尝试更多样化的策略"
        elif improvement < 0.2:
            return "微调学习参数，优化现有策略"
        else:
            return "保持当前学习策略，效果很好"
    
    def optimize_learning_rate(self) -> float:
        """优化学习率"""
        # 简化的自适应学习率调整
        recent_rewards = [e.reward for e in self.evolution.experience_buffer[-50:]]
        if not recent_rewards:
            return 0.1
        
        variance = sum((r - sum(recent_rewards)/len(recent_rewards))**2 for r in recent_rewards) / len(recent_rewards)
        
        # 如果方差大，降低学习率；如果方差小，可以适当增加
        if variance > 0.3:
            return max(0.01, self.evolution.learning_rate * 0.9)
        elif variance < 0.1:
            return min(0.5, self.evolution.learning_rate * 1.1)
        
        return self.evolution.learning_rate


# 便捷函数
def create_self_evolution_system(brain=None) -> SelfEvolutionEngine:
    """创建自我进化系统"""
    engine = SelfEvolutionEngine(brain_reference=brain)
    
    # 尝试加载之前的状态
    try:
        engine.load_state("data/evolution_state.json")
    except:
        pass
    
    return engine
