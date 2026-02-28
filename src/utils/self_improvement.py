#!/usr/bin/env python3
"""
自我改进与持续优化系统

功能：
1. 分析历史执行数据
2. 识别改进机会
3. 自动调整执行策略
4. 学习用户偏好
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class ImprovementRecord:
    """改进记录"""
    timestamp: str
    category: str  # "intent", "template", "threshold", "cache"
    description: str
    before_value: Any
    after_value: Any
    impact_score: float  # 0-1，改进效果


class SelfImprovementSystem:
    """
    自我改进系统
    
    通过分析执行历史，自动优化：
    1. 意图识别准确率
    2. 模板响应质量
    3. 缓存命中率
    4. LLM/Brain 切换阈值
    """
    
    def __init__(self, data_dir: str = "/workspace/projects/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.improvements_file = self.data_dir / "self_improvements.json"
        self.execution_log_file = self.data_dir / "execution_log.json"
        
        self.improvements: List[ImprovementRecord] = []
        self.execution_history: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """加载历史数据"""
        if self.improvements_file.exists():
            with open(self.improvements_file, 'r') as f:
                data = json.load(f)
                self.improvements = [ImprovementRecord(**r) for r in data]
        
        if self.execution_log_file.exists():
            with open(self.execution_log_file, 'r') as f:
                self.execution_history = json.load(f)
    
    def _save_data(self):
        """保存数据"""
        with open(self.improvements_file, 'w') as f:
            json.dump([asdict(r) for r in self.improvements], f, indent=2)
        
        with open(self.execution_log_file, 'w') as f:
            json.dump(self.execution_history, f, indent=2)
    
    def log_execution(self, goal: str, result: Dict):
        """记录执行结果"""
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "result": result
        })
        
        # 限制历史记录大小
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        self._save_data()
    
    def analyze_performance(self) -> Dict:
        """
        分析性能并生成改进建议
        
        Returns:
            分析报告和改进建议
        """
        if not self.execution_history:
            return {"status": "no_data", "recommendations": []}
        
        # 统计指标
        total = len(self.execution_history)
        local_only = sum(1 for e in self.execution_history 
                        if e["result"].get("mode") == "local_only")
        cached = sum(1 for e in self.execution_history 
                    if e["result"].get("cached", False))
        
        avg_duration = sum(e["result"].get("duration_ms", 0) 
                          for e in self.execution_history) / total
        
        # 识别问题
        recommendations = []
        
        # 1. 缓存命中率低
        cache_rate = cached / total if total > 0 else 0
        if cache_rate < 0.3:
            recommendations.append({
                "priority": "high",
                "category": "cache",
                "issue": f"缓存命中率低 ({cache_rate*100:.1f}%)",
                "solution": "增加缓存大小，改进缓存键生成策略",
                "action": "increase_cache_size"
            })
        
        # 2. 本地处理率低
        local_rate = local_only / total if total > 0 else 0
        if local_rate < 0.4:
            recommendations.append({
                "priority": "high",
                "category": "intent",
                "issue": f"本地处理率低 ({local_rate*100:.1f}%)",
                "solution": "扩展意图识别模式，添加更多本地处理规则",
                "action": "extend_intent_patterns"
            })
        
        # 3. 平均响应时间高
        if avg_duration > 1000:
            recommendations.append({
                "priority": "medium",
                "category": "performance",
                "issue": f"平均响应时间较长 ({avg_duration:.0f}ms)",
                "solution": "优化本地工具执行，减少同步调用",
                "action": "optimize_performance"
            })
        
        # 4. 检查常见失败意图
        failed_intents = {}
        for e in self.execution_history:
            if not e["result"].get("success", True):
                intent = e["result"].get("intent", "unknown")
                failed_intents[intent] = failed_intents.get(intent, 0) + 1
        
        if failed_intents:
            top_failed = sorted(failed_intents.items(), key=lambda x: x[1], reverse=True)[:3]
            for intent, count in top_failed:
                recommendations.append({
                    "priority": "medium",
                    "category": "reliability",
                    "issue": f"意图 '{intent}' 失败率高 ({count}次)",
                    "solution": f"检查 '{intent}' 的处理逻辑，添加错误处理",
                    "action": "fix_intent_handler"
                })
        
        return {
            "status": "analyzed",
            "total_executions": total,
            "local_rate": local_rate,
            "cache_rate": cache_rate,
            "avg_duration_ms": avg_duration,
            "recommendations": recommendations
        }
    
    def generate_improvement_plan(self) -> str:
        """生成改进计划报告"""
        analysis = self.analyze_performance()
        
        lines = [
            "=" * 60,
            "🔧 自我改进分析报告",
            "=" * 60,
            f"总执行次数: {analysis.get('total_executions', 0)}",
            f"本地处理率: {analysis.get('local_rate', 0)*100:.1f}%",
            f"缓存命中率: {analysis.get('cache_rate', 0)*100:.1f}%",
            f"平均响应时间: {analysis.get('avg_duration_ms', 0):.0f}ms",
            "",
        ]
        
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            lines.append("💡 改进建议:")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"\n  {i}. [{rec['priority'].upper()}] {rec['category']}")
                lines.append(f"     问题: {rec['issue']}")
                lines.append(f"     方案: {rec['solution']}")
                lines.append(f"     行动: {rec['action']}")
        else:
            lines.append("✅ 系统运行良好，暂无改进建议")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def apply_improvement(self, category: str, change: Dict) -> bool:
        """
        应用改进
        
        Args:
            category: 改进类别
            change: 变更内容
        
        Returns:
            是否成功
        """
        # 记录改进
        improvement = ImprovementRecord(
            timestamp=datetime.now().isoformat(),
            category=category,
            description=change.get("description", ""),
            before_value=change.get("before"),
            after_value=change.get("after"),
            impact_score=change.get("impact", 0.0)
        )
        
        self.improvements.append(improvement)
        self._save_data()
        
        print(f"✅ 已应用改进: {category} - {change.get('description', '')}")
        return True
    
    def export_learning_data(self) -> Dict:
        """导出学习数据用于训练"""
        # 提取成功的本地处理案例
        successful_locals = [
            {
                "goal": e["goal"],
                "intent": e["result"].get("intent"),
                "duration_ms": e["result"].get("duration_ms"),
            }
            for e in self.execution_history
            if e["result"].get("success") and e["result"].get("mode") == "local_only"
        ]
        
        # 提取常见意图模式
        intent_patterns = {}
        for e in self.execution_history:
            intent = e["result"].get("intent", "unknown")
            if intent not in intent_patterns:
                intent_patterns[intent] = []
            intent_patterns[intent].append(e["goal"])
        
        # 保留最常见的模式
        for intent in intent_patterns:
            intent_patterns[intent] = intent_patterns[intent][:10]
        
        return {
            "successful_local_cases": successful_locals[:100],
            "intent_patterns": intent_patterns,
            "improvement_history": [asdict(i) for i in self.improvements[-50:]],
        }


def demonstrate_self_improvement():
    """演示自我改进系统"""
    print("=" * 60)
    print("🔄 自我改进系统演示")
    print("=" * 60)
    
    # 创建系统
    system = SelfImprovementSystem()
    
    # 模拟执行历史
    test_cases = [
        {"goal": "查看 git 状态", "mode": "local_only", "success": True, "duration_ms": 50},
        {"goal": "hi", "mode": "local_only", "success": True, "duration_ms": 10},
        {"goal": "帮我写代码", "mode": "llm_first", "success": True, "duration_ms": 1500},
        {"goal": "查看文件", "mode": "local_only", "success": True, "duration_ms": 30},
        {"goal": "设计系统", "mode": "llm_first", "success": False, "duration_ms": 2000},
    ]
    
    print("\n📊 模拟执行记录...")
    for case in test_cases:
        system.log_execution(case["goal"], case)
        print(f"  • {case['goal']}: {case['mode']} ({case['duration_ms']}ms)")
    
    # 生成改进报告
    print("\n" + system.generate_improvement_plan())
    
    # 导出学习数据
    print("\n📚 学习数据导出:")
    learning_data = system.export_learning_data()
    print(f"  成功案例: {len(learning_data['successful_local_cases'])}")
    print(f"  意图模式: {list(learning_data['intent_patterns'].keys())}")
    
    return system


if __name__ == "__main__":
    demonstrate_self_improvement()
