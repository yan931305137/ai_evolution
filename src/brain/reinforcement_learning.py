"""
强化学习系统 - Reinforcement Learning System

实现基于 Q-Learning 的强化学习能力，使 Brain 能够从长期交互中学习最优策略。
支持：
- Q-Learning 算法
- 策略评估与改进
- 经验回放
- 多策略管理
"""

import json
import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
from datetime import datetime
import hashlib


@dataclass
class State:
    """状态表示"""
    id: str
    features: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, State):
            return self.id == other.id
        return False


@dataclass
class Action:
    """动作表示"""
    id: str
    name: str
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Action):
            return self.id == other.id
        return False


@dataclass
class Experience:
    """经验样本"""
    state: State
    action: Action
    reward: float
    next_state: State
    done: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "state_id": self.state.id,
            "action_id": self.action.id,
            "reward": self.reward,
            "next_state_id": self.next_state.id,
            "done": self.done,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class Policy:
    """策略"""
    name: str
    action_selector: Callable[[State, List[Action]], Action]
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


class QLearningAgent:
    """
    Q-Learning 智能体
    
    使用 Q-Learning 算法学习最优策略
    """
    
    def __init__(
        self,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1,           # 探索率
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Q表: {(state_id, action_id): q_value}
        self.q_table: Dict[Tuple[str, str], float] = defaultdict(float)
        
        # 状态访问次数
        self.state_visits: Dict[str, int] = defaultdict(int)
        
        # 经验回放池
        self.experience_buffer: deque = deque(maxlen=10000)
        
        # 训练统计
        self.training_stats = {
            "total_episodes": 0,
            "total_steps": 0,
            "total_reward": 0.0,
            "avg_reward_history": deque(maxlen=100),
        }
    
    def get_q_value(self, state_id: str, action_id: str) -> float:
        """获取 Q 值"""
        return self.q_table.get((state_id, action_id), 0.0)
    
    def get_best_action(self, state: State, available_actions: List[Action]) -> Action:
        """
        获取当前状态下的最优动作（考虑探索）
        """
        if not available_actions:
            raise ValueError("No available actions")
        
        # Epsilon-greedy 策略
        if random.random() < self.epsilon:
            # 探索：随机选择
            return random.choice(available_actions)
        
        # 利用：选择 Q 值最高的动作
        q_values = [
            (action, self.get_q_value(state.id, action.id))
            for action in available_actions
        ]
        
        # 处理平局：随机选择最高 Q 值的动作
        max_q = max(qv[1] for qv in q_values)
        best_actions = [a for a, q in q_values if abs(q - max_q) < 1e-6]
        return random.choice(best_actions)
    
    def get_action_values(self, state: State, available_actions: List[Action]) -> Dict[str, float]:
        """获取状态下所有动作的 Q 值"""
        return {
            action.id: self.get_q_value(state.id, action.id)
            for action in available_actions
        }
    
    def update(
        self,
        state: State,
        action: Action,
        reward: float,
        next_state: State,
        next_actions: List[Action],
        done: bool = False
    ):
        """
        更新 Q 值
        """
        # 当前 Q 值
        current_q = self.get_q_value(state.id, action.id)
        
        # 计算 TD 目标
        if done or not next_actions:
            target = reward
        else:
            # 下一状态的最大 Q 值
            next_q_values = [
                self.get_q_value(next_state.id, a.id)
                for a in next_actions
            ]
            max_next_q = max(next_q_values) if next_q_values else 0
            target = reward + self.discount_factor * max_next_q
        
        # Q 值更新公式
        new_q = current_q + self.learning_rate * (target - current_q)
        self.q_table[(state.id, action.id)] = new_q
        
        # 更新状态访问次数
        self.state_visits[state.id] += 1
        
        # 记录经验
        experience = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )
        self.experience_buffer.append(experience)
        
        # 更新训练统计
        self.training_stats["total_steps"] += 1
        self.training_stats["total_reward"] += reward
    
    def decay_epsilon(self):
        """衰减探索率"""
        self.epsilon = max(
            self.epsilon_min,
            self.epsilon * self.epsilon_decay
        )
    
    def replay_experiences(self, batch_size: int = 32):
        """
        经验回放
        
        从经验池中随机采样并更新
        """
        if len(self.experience_buffer) < batch_size:
            return
        
        batch = random.sample(list(self.experience_buffer), batch_size)
        
        for exp in batch:
            # 这里简化处理，实际应该重新获取 next_actions
            self.update(
                state=exp.state,
                action=exp.action,
                reward=exp.reward,
                next_state=exp.next_state,
                next_actions=[],  # 实际应用时需要提供
                done=exp.done
            )
    
    def get_policy(self, available_actions: List[Action]) -> Dict[str, str]:
        """
        获取当前策略（状态 -> 动作映射）
        """
        policy = {}
        
        # 收集所有状态
        states = set()
        for s_id, _ in self.q_table.keys():
            states.add(s_id)
        
        # 为每个状态选择最优动作
        for state_id in states:
            action_values = {
                a.id: self.get_q_value(state_id, a.id)
                for a in available_actions
            }
            if action_values:
                best_action = max(action_values, key=action_values.get)
                policy[state_id] = best_action
        
        return policy
    
    def save(self, filepath: str):
        """保存模型"""
        data = {
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "epsilon_min": self.epsilon_min,
            "q_table": {f"{k[0]}::{k[1]}": v for k, v in self.q_table.items()},
            "state_visits": dict(self.state_visits),
            "training_stats": {
                k: list(v) if isinstance(v, deque) else v
                for k, v in self.training_stats.items()
            },
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self, filepath: str):
        """加载模型"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.learning_rate = data.get("learning_rate", 0.1)
        self.discount_factor = data.get("discount_factor", 0.9)
        self.epsilon = data.get("epsilon", 0.1)
        self.epsilon_decay = data.get("epsilon_decay", 0.995)
        self.epsilon_min = data.get("epsilon_min", 0.01)
        
        # 恢复 Q 表
        self.q_table.clear()
        for key, value in data.get("q_table", {}).items():
            parts = key.split("::")
            if len(parts) == 2:
                self.q_table[(parts[0], parts[1])] = value
        
        # 恢复状态访问次数
        self.state_visits = defaultdict(int, data.get("state_visits", {}))
        
        # 恢复训练统计
        stats = data.get("training_stats", {})
        self.training_stats = {
            "total_episodes": stats.get("total_episodes", 0),
            "total_steps": stats.get("total_steps", 0),
            "total_reward": stats.get("total_reward", 0.0),
            "avg_reward_history": deque(
                stats.get("avg_reward_history", []),
                maxlen=100
            ),
        }


class ReinforcementLearningSystem:
    """
    强化学习系统
    
    管理多个 RL 智能体，支持不同任务场景
    """
    
    def __init__(self):
        self.agents: Dict[str, QLearningAgent] = {}
        self.active_policies: Dict[str, Dict] = {}
        
        # 预定义任务场景
        self.task_scenarios = {
            "response_selection": "回复选择优化",
            "tool_selection": "工具选择优化",
            "planning": "规划策略优化",
            "emotion_response": "情感回应优化",
        }
    
    def create_agent(self, task_id: str, **kwargs) -> QLearningAgent:
        """创建新的 RL 智能体"""
        agent = QLearningAgent(**kwargs)
        self.agents[task_id] = agent
        return agent
    
    def get_agent(self, task_id: str) -> Optional[QLearningAgent]:
        """获取智能体"""
        return self.agents.get(task_id)
    
    def select_response_strategy(
        self,
        context: Dict[str, Any],
        available_strategies: List[str]
    ) -> str:
        """
        选择最优回复策略
        
        用于优化 L1-L5 处理级别的选择
        """
        agent = self.get_agent("response_selection")
        if not agent:
            # 首次使用，创建智能体
            agent = self.create_agent("response_selection")
        
        # 构建状态
        state = self._build_response_state(context)
        
        # 构建动作
        actions = [
            Action(id=s, name=s, description=f"Use {s} strategy")
            for s in available_strategies
        ]
        
        # 选择最优策略
        best_action = agent.get_best_action(state, actions)
        return best_action.id
    
    def _build_response_state(self, context: Dict) -> State:
        """构建回复选择的状态表示"""
        # 提取关键特征
        features = {
            "input_length": len(context.get("input", "")),
            "has_code": bool(context.get("has_code", False)),
            "has_question": "?" in context.get("input", ""),
            "user_emotion": context.get("emotion", "neutral"),
            "previous_interaction_count": context.get("history_length", 0),
            "domain": context.get("domain", "general"),
        }
        
        # 生成状态ID
        state_id = hashlib.md5(
            json.dumps(features, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        return State(
            id=state_id,
            features=features,
            description=f"Response context: {features}"
        )
    
    def learn_from_feedback(
        self,
        task_id: str,
        context: Dict,
        selected_strategy: str,
        reward: float
    ):
        """
        从反馈中学习
        
        Args:
            reward: 用户反馈 (-1 到 1)
        """
        agent = self.get_agent(task_id)
        if not agent:
            return
        
        # 重建状态和动作
        state = self._build_response_state(context)
        action = Action(id=selected_strategy, name=selected_strategy)
        
        # 下一状态（简化处理，实际应该基于新上下文）
        next_state = State(id="next_state", features={})
        
        # 更新 Q 值
        agent.update(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            next_actions=[],  # 简化处理
            done=True
        )
        
        # 衰减探索率
        agent.decay_epsilon()
    
    def get_learning_stats(self, task_id: Optional[str] = None) -> Dict:
        """获取学习统计"""
        if task_id:
            agent = self.get_agent(task_id)
            if agent:
                return {
                    "task_id": task_id,
                    "epsilon": agent.epsilon,
                    "total_steps": agent.training_stats["total_steps"],
                    "total_reward": agent.training_stats["total_reward"],
                    "avg_reward": (
                        agent.training_stats["total_reward"] / 
                        max(1, agent.training_stats["total_steps"])
                    ),
                    "state_coverage": len(agent.state_visits),
                }
            return {}
        
        # 返回所有智能体统计
        return {
            task_id: self.get_learning_stats(task_id)
            for task_id in self.agents.keys()
        }
    
    def export_policy(self, task_id: str) -> Dict:
        """导出学习到的策略"""
        agent = self.get_agent(task_id)
        if not agent:
            return {}
        
        # 这里简化处理，实际应该获取所有可能的动作
        policy = {}
        for (state_id, action_id), q_value in agent.q_table.items():
            if state_id not in policy or q_value > policy.get(state_id, (None, 0))[1]:
                policy[state_id] = (action_id, q_value)
        
        return {
            "task_id": task_id,
            "policy": {s: a for s, (a, _) in policy.items()},
            "export_time": datetime.now().isoformat(),
        }
    
    def save_all(self, directory: str):
        """保存所有智能体"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        for task_id, agent in self.agents.items():
            filepath = os.path.join(directory, f"{task_id}_agent.json")
            agent.save(filepath)
    
    def load_all(self, directory: str):
        """加载所有智能体"""
        import os
        import glob
        
        pattern = os.path.join(directory, "*_agent.json")
        for filepath in glob.glob(pattern):
            task_id = os.path.basename(filepath).replace("_agent.json", "")
            agent = QLearningAgent()
            agent.load(filepath)
            self.agents[task_id] = agent


# 与 Brain 的集成函数

def create_rl_enhanced_brain():
    """
    创建带有强化学习能力的 Brain
    """
    from src.brain.human_level_brain import HumanLevelBrain
    
    class RLEnhancedBrain(HumanLevelBrain):
        """强化学习增强的大脑"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.rl_system = ReinforcementLearningSystem()
            self.current_context = {}
            self.selected_strategy = None
        
        def select_processing_level(self, user_input: str) -> str:
            """
            使用 RL 选择最佳处理级别
            """
            # 构建上下文
            self.current_context = {
                "input": user_input,
                "has_code": any(kw in user_input.lower() for kw in ["code", "bug", "error"]),
                "emotion": self.detect_emotion(user_input),
                "history_length": len(self.conversation_history),
                "domain": self.classify_domain(user_input),
            }
            
            # 可用的处理策略
            strategies = ["L1_template", "L2_rules", "L3_semantic", "L4_inference", "L5_llm"]
            
            # 使用 RL 选择
            strategy = self.rl_system.select_response_strategy(
                self.current_context,
                strategies
            )
            
            self.selected_strategy = strategy
            return strategy
        
        def learn_from_user_feedback(self, feedback: float):
            """
            从用户反馈中学习
            
            feedback: -1 (非常不满意) 到 1 (非常满意)
            """
            if self.selected_strategy and self.current_context:
                self.rl_system.learn_from_feedback(
                    task_id="response_selection",
                    context=self.current_context,
                    selected_strategy=self.selected_strategy,
                    reward=feedback
                )
        
        def detect_emotion(self, text: str) -> str:
            """检测文本情感"""
            # 简化实现
            positive_words = ["好", "棒", "优秀", "感谢", "喜欢"]
            negative_words = ["差", "糟", "不好", "讨厌", "错误"]
            
            for word in positive_words:
                if word in text:
                    return "positive"
            for word in negative_words:
                if word in text:
                    return "negative"
            return "neutral"
        
        def classify_domain(self, text: str) -> str:
            """分类领域"""
            # 简化实现
            if any(kw in text.lower() for kw in ["python", "code", "programming", "bug"]):
                return "technical"
            elif any(kw in text.lower() for kw in ["feel", "sad", "happy", "emotion"]):
                return "emotional"
            return "general"
        
        def get_rl_stats(self) -> Dict:
            """获取 RL 学习统计"""
            return self.rl_system.get_learning_stats("response_selection")
    
    return RLEnhancedBrain()


# 全局 RL 系统实例
_rl_system = None


def get_rl_system() -> ReinforcementLearningSystem:
    """获取全局 RL 系统实例"""
    global _rl_system
    if _rl_system is None:
        _rl_system = ReinforcementLearningSystem()
    return _rl_system
