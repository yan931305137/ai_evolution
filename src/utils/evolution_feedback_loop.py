"""
进化反馈循环 (Evolution Feedback Loop)

完整的创造→评估→应用→进化闭环
"""
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from src.utils.creativity import CreativeIdea
from src.utils.idea_evaluator import IdeaEvaluator, IdeaEvaluation
from src.utils.idea_applicator import IdeaApplicator, ApplicationResult
from src.utils.evolution_goal_manager import EvolutionGoalManager


@dataclass
class EvolutionCycle:
    """进化周期记录"""
    cycle_id: str
    timestamp: float
    stage: str  # create / evaluate / apply / evolve
    input_data: Dict
    output_data: Dict
    duration: float
    success: bool
    feedback: str


class EvolutionFeedbackLoop:
    """
    进化反馈循环
    
    实现完整的创造→评估→应用→进化闭环
    
    流程:
    1. 创造 (Create): 产生新想法
    2. 评估 (Evaluate): 评估想法质量和价值
    3. 应用 (Apply): 将优质想法转化为实际行动
    4. 进化 (Evolve): 根据应用结果调整进化策略
    """
    
    def __init__(
        self,
        workspace_dir: str = "workspace/evolution",
        config_path: str = None
    ):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各模块
        self.goal_manager = EvolutionGoalManager(config_path)
        self.evaluator = IdeaEvaluator()
        self.applicator = IdeaApplicator(str(self.workspace_dir))
        
        # 周期记录
        self.cycles: List[EvolutionCycle] = []
        self.current_cycle: Optional[EvolutionCycle] = None
        
        # 统计
        self.stats = {
            "total_ideas_created": 0,
            "total_ideas_evaluated": 0,
            "total_ideas_applied": 0,
            "total_cycles_completed": 0,
            "avg_evaluation_score": 0.0,
            "evolution_velocity": 0.0  # 进化速度
        }
        
        # 加载历史
        self._load_stats()
    
    def _load_stats(self):
        """加载统计"""
        stats_file = self.workspace_dir / "evolution_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
            except:
                pass
    
    def _save_stats(self):
        """保存统计"""
        stats_file = self.workspace_dir / "evolution_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
    
    def run_full_cycle(self, ideas: List[CreativeIdea] = None) -> Dict[str, Any]:
        """
        运行完整的进化周期
        
        Args:
            ideas: 可选的预设想法列表，如果没有则使用已有想法
            
        Returns:
            Dict: 周期执行结果
        """
        cycle_id = f"cycle_{int(time.time())}"
        start_time = time.time()
        
        results = {
            "cycle_id": cycle_id,
            "stages": {},
            "summary": {}
        }
        
        print(f"\n🔄 启动进化周期 {cycle_id}")
        print("=" * 60)
        
        # Stage 1: 创造 (如果提供了新想法)
        if ideas:
            results["stages"]["create"] = self._stage_create(ideas)
        
        # Stage 2: 评估
        results["stages"]["evaluate"] = self._stage_evaluate()
        
        # Stage 3: 应用
        results["stages"]["apply"] = self._stage_apply()
        
        # Stage 4: 进化
        results["stages"]["evolve"] = self._stage_evolve()
        
        # 更新统计
        duration = time.time() - start_time
        self.stats["total_cycles_completed"] += 1
        self._save_stats()
        
        # 生成摘要
        results["summary"] = self._generate_summary(results, duration)
        
        print(f"\n✅ 进化周期完成，总耗时: {duration:.2f}s")
        self._print_cycle_summary(results)
        
        return results
    
    def _stage_create(self, ideas: List[CreativeIdea]) -> Dict:
        """创造阶段：记录新产生的想法"""
        start = time.time()
        print("\n🎨 [Stage 1/4] 创造阶段")
        
        self.stats["total_ideas_created"] += len(ideas)
        
        # 记录想法
        for idea in ideas:
            # 处理不同的想法类型
            if hasattr(idea, 'idea'):
                content = idea.idea
            elif hasattr(idea, 'content'):
                content = idea.content
            else:
                content = str(idea)
            print(f"  💡 {content[:60]}...")
        
        return {
            "ideas_count": len(ideas),
            "duration": time.time() - start
        }
    
    def _stage_evaluate(self) -> Dict:
        """评估阶段：评估待处理的想法"""
        start = time.time()
        print("\n📊 [Stage 2/4] 评估阶段")
        
        # 获取待评估的想法（这里可以从历史或数据库中获取）
        # 简化实现：使用评估器的历史记录
        
        if not self.evaluator.evaluation_history:
            print("  没有待评估的想法")
            return {"evaluated": 0, "duration": time.time() - start}
        
        # 统计
        total = len(self.evaluator.evaluation_history)
        apply_count = sum(
            1 for e in self.evaluator.evaluation_history 
            if e.recommendation == "apply"
        )
        
        avg_score = sum(e.overall_score for e in self.evaluator.evaluation_history) / total
        
        self.stats["total_ideas_evaluated"] += total
        self.stats["avg_evaluation_score"] = avg_score
        
        print(f"  已评估: {total} 个想法")
        print(f"  推荐应用: {apply_count} 个")
        print(f"  平均得分: {avg_score:.1f}")
        
        return {
            "evaluated": total,
            "apply_recommended": apply_count,
            "avg_score": avg_score,
            "duration": time.time() - start
        }
    
    def _stage_apply(self) -> Dict:
        """应用阶段：应用评估通过的想法"""
        start = time.time()
        print("\n🔧 [Stage 3/4] 应用阶段")
        
        # 获取推荐应用的想法
        approved_ideas = [
            e for e in self.evaluator.evaluation_history
            if e.recommendation == "apply"
        ]
        
        if not approved_ideas:
            print("  没有待应用的想法")
            return {"applied": 0, "duration": time.time() - start}
        
        applied_count = 0
        success_count = 0
        
        for eval_result in approved_ideas[:3]:  # 每周期最多应用3个
            app_result = self.applicator.apply(
                eval_result.idea_id,
                eval_result.idea_content,
                eval_result.to_dict()
            )
            
            applied_count += 1
            if app_result.status.value == "success":
                success_count += 1
                print(f"  ✅ 已应用: {app_result.idea_content[:40]}...")
            else:
                print(f"  ❌ 失败: {app_result.error_message}")
        
        self.stats["total_ideas_applied"] += applied_count
        
        return {
            "applied": applied_count,
            "success": success_count,
            "duration": time.time() - start
        }
    
    def _stage_evolve(self) -> Dict:
        """进化阶段：根据反馈调整进化策略"""
        start = time.time()
        print("\n🌱 [Stage 4/4] 进化阶段")
        
        # 获取应用统计
        app_stats = self.applicator.get_application_stats()
        
        # 分析反馈
        feedback = self._analyze_evolution_feedback()
        
        # 调整目标进度
        self._adjust_goal_progress()
        
        # 计算进化速度
        if app_stats["total"] > 0:
            velocity = app_stats["success"] / app_stats["total"]
            self.stats["evolution_velocity"] = velocity
        
        print(f"  应用成功率: {app_stats.get('success_rate', 0):.1%}")
        print(f"  进化速度: {self.stats['evolution_velocity']:.2f}")
        print(f"  调整目标: {len(self.goal_manager.get_active_goals())} 个")
        
        return {
            "feedback": feedback,
            "velocity": self.stats["evolution_velocity"],
            "duration": time.time() - start
        }
    
    def _analyze_evolution_feedback(self) -> Dict[str, Any]:
        """分析进化反馈"""
        feedback = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }
        
        # 分析成功的应用
        successful = [
            r for r in self.applicator.application_history
            if r.status.value == "success"
        ]
        
        if successful:
            # 找出成功模式
            types = {}
            for r in successful:
                t = r.app_type.value
                types[t] = types.get(t, 0) + 1
            
            most_successful = max(types.items(), key=lambda x: x[1])[0]
            feedback["strengths"].append(f"在 {most_successful} 类型应用中表现良好")
        
        # 分析失败
        failed = [
            r for r in self.applicator.application_history
            if r.status.value == "failed"
        ]
        
        if len(failed) > len(self.applicator.application_history) * 0.3:
            feedback["weaknesses"].append("应用失败率较高，需要改进实现机制")
        
        # 基于评估分数
        if self.stats["avg_evaluation_score"] < 60:
            feedback["opportunities"].append("想法质量有提升空间，可以优化创造过程")
        
        return feedback
    
    def _adjust_goal_progress(self):
        """调整目标进度"""
        # 根据应用结果调整目标进度
        app_stats = self.applicator.get_application_stats()
        
        # 检查是否有足够的应用记录
        success_rate = app_stats.get("success_rate", 0)
        if success_rate > 0.8:
            # 高成功率，加速目标进度
            for name, goal in self.goal_manager.goals.items():
                if goal.enabled:
                    increment = 2.0 * goal.weight
                    new_value = min(goal.current_value + increment, goal.target_value)
                    self.goal_manager.update_goal_progress(name, new_value)
    
    def _generate_summary(self, results: Dict, duration: float) -> Dict:
        """生成周期摘要"""
        stages = results["stages"]
        
        return {
            "total_duration": duration,
            "ideas_flow": {
                "created": stages.get("create", {}).get("ideas_count", 0),
                "evaluated": stages.get("evaluate", {}).get("evaluated", 0),
                "applied": stages.get("apply", {}).get("applied", 0),
                "success": stages.get("apply", {}).get("success", 0)
            },
            "evolution_metrics": {
                "velocity": self.stats["evolution_velocity"],
                "avg_score": self.stats["avg_evaluation_score"]
            },
            "goal_progress": self.goal_manager.get_evolution_progress()
        }
    
    def _print_cycle_summary(self, results: Dict):
        """打印周期摘要"""
        summary = results["summary"]
        flow = summary["ideas_flow"]
        
        print("\n📈 周期摘要")
        print("-" * 60)
        print(f"想法流: {flow['created']} 创造 → {flow['evaluated']} 评估 → {flow['applied']} 应用 ({flow['success']} 成功)")
        print(f"进化速度: {summary['evolution_metrics']['velocity']:.2f}")
        print(f"目标进度: {summary['goal_progress']['overall_progress']:.1f}%")
    
    def get_full_report(self) -> Dict[str, Any]:
        """获取完整报告"""
        return {
            "evolution_stats": self.stats,
            "goals": self.goal_manager.get_evolution_progress(),
            "evaluation_stats": self.evaluator.get_evaluation_stats(),
            "application_stats": self.applicator.get_application_stats(),
            "recent_cycles": len(self.cycles)
        }
    
    def configure_goal(self, name: str, **kwargs):
        """配置进化目标"""
        from src.utils.evolution_goal_manager import EvolutionGoal, EvolutionDimension
        
        if name not in self.goal_manager.goals:
            # 创建新目标
            goal = EvolutionGoal(
                name=name,
                dimension=EvolutionDimension(kwargs.get("dimension", "capability")),
                description=kwargs.get("description", ""),
                target_value=kwargs.get("target", 80.0),
                weight=kwargs.get("weight", 1.0),
                priority=kwargs.get("priority", 3)
            )
            self.goal_manager.add_goal(goal)
        else:
            # 更新现有目标
            goal = self.goal_manager.goals[name]
            for key, value in kwargs.items():
                if hasattr(goal, key):
                    setattr(goal, key, value)
            self.goal_manager.save_config()
        
        print(f"✅ 已配置进化目标: {name}")


# 便捷函数
def run_evolution_cycle(ideas: List[CreativeIdea] = None) -> Dict:
    """运行进化周期"""
    loop = EvolutionFeedbackLoop()
    return loop.run_full_cycle(ideas)


if __name__ == "__main__":
    # 测试完整循环
    loop = EvolutionFeedbackLoop()
    
    # 显示当前配置
    loop.goal_manager.print_config()
    
    # 运行空循环（测试）
    results = loop.run_full_cycle()
    
    print("\n完整报告:")
    report = loop.get_full_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
