"""
进化闭环管理命令 (Evolution Loop Management Commands)
用于查看和管理进化目标、运行进化周期
"""
import click
import json
from src.utils.evolution_goal_manager import EvolutionGoalManager, EvolutionGoal, EvolutionDimension
from src.utils.evolution_feedback_loop import EvolutionFeedbackLoop


@click.group(name="evolution")
def evolution_cli():
    """进化闭环管理命令"""
    pass


@evolution_cli.command(name="goals")
@click.option('--config', '-c', default='config/evolution_goals.yaml', help='配置文件路径')
def show_goals(config):
    """显示当前进化目标"""
    manager = EvolutionGoalManager(config)
    manager.print_config()


@evolution_cli.command(name="add-goal")
@click.argument('name')
@click.option('--dimension', '-d', default='capability', 
              type=click.Choice(['capability', 'knowledge', 'efficiency', 'creativity', 'social', 'adaptation']))
@click.option('--description', '-desc', default='')
@click.option('--target', '-t', default=80.0, type=float)
@click.option('--weight', '-w', default=1.0, type=float)
@click.option('--priority', '-p', default=3, type=int)
@click.option('--config', '-c', default='config/evolution_goals.yaml')
def add_goal(name, dimension, description, target, weight, priority, config):
    """添加新的进化目标"""
    manager = EvolutionGoalManager(config)
    
    goal = EvolutionGoal(
        name=name,
        dimension=EvolutionDimension(dimension),
        description=description or f"{name}目标",
        target_value=target,
        weight=weight,
        priority=priority
    )
    
    manager.add_goal(goal)
    click.echo(f"✅ 已添加进化目标: {name}")


@evolution_cli.command(name="remove-goal")
@click.argument('name')
@click.option('--config', '-c', default='config/evolution_goals.yaml')
def remove_goal(name, config):
    """移除进化目标"""
    manager = EvolutionGoalManager(config)
    
    if name not in manager.goals:
        click.echo(f"❌ 目标不存在: {name}")
        return
    
    manager.remove_goal(name)
    click.echo(f"✅ 已移除进化目标: {name}")


@evolution_cli.command(name="set-strategy")
@click.argument('strategy', type=click.Choice(['exploration', 'exploitation', 'balanced', 'focused']))
@click.option('--config', '-c', default='config/evolution_goals.yaml')
def set_strategy(strategy, config):
    """设置进化策略"""
    from src.utils.evolution_goal_manager import EvolutionStrategy
    
    manager = EvolutionGoalManager(config)
    manager.strategy = EvolutionStrategy(strategy)
    manager.save_config()
    
    strategy_desc = {
        'exploration': '探索优先 - 更激进的尝试新想法',
        'exploitation': '利用优先 - 更保守地优化现有能力',
        'balanced': '平衡策略 - 在探索和利用之间平衡',
        'focused': '专注策略 - 专注于优先级最高的目标'
    }
    
    click.echo(f"✅ 已设置进化策略: {strategy}")
    click.echo(f"   {strategy_desc[strategy]}")


@evolution_cli.command(name="run")
@click.option('--config', '-c', default='config/evolution_goals.yaml')
def run_cycle(config):
    """运行一个完整的进化周期"""
    click.echo("🔄 启动进化周期...")
    
    loop = EvolutionFeedbackLoop(config_path=config)
    results = loop.run_full_cycle()
    
    # 显示结果
    summary = results.get("summary", {})
    flow = summary.get("ideas_flow", {})
    
    click.echo("\n📊 周期结果:")
    click.echo(f"  想法流: {flow.get('created', 0)} → {flow.get('evaluated', 0)} → {flow.get('applied', 0)}")
    click.echo(f"  成功率: {flow.get('success', 0)}/{flow.get('applied', 0)}")
    click.echo(f"  进化速度: {summary.get('evolution_metrics', {}).get('velocity', 0):.2f}")


@evolution_cli.command(name="status")
@click.option('--config', '-c', default='config/evolution_goals.yaml')
def show_status(config):
    """显示进化闭环状态"""
    loop = EvolutionFeedbackLoop(config_path=config)
    report = loop.get_full_report()
    
    click.echo("\n📈 进化闭环状态报告")
    click.echo("=" * 60)
    
    # 统计信息
    stats = report.get("evolution_stats", {})
    click.echo(f"\n累计统计:")
    click.echo(f"  想法创造: {stats.get('total_ideas_created', 0)}")
    click.echo(f"  想法评估: {stats.get('total_ideas_evaluated', 0)}")
    click.echo(f"  想法应用: {stats.get('total_ideas_applied', 0)}")
    click.echo(f"  完成周期: {stats.get('total_cycles_completed', 0)}")
    
    # 评估统计
    eval_stats = report.get("evaluation_stats", {})
    click.echo(f"\n评估统计:")
    click.echo(f"  已评估: {eval_stats.get('total', 0)}")
    if eval_stats.get('total', 0) > 0:
        click.echo(f"  平均得分: {eval_stats.get('avg_score', 0):.1f}")
        rec_dist = eval_stats.get('recommendation_distribution', {})
        click.echo(f"  推荐应用: {rec_dist.get('apply', 0)}")
        click.echo(f"  建议改进: {rec_dist.get('refine', 0)}")
        click.echo(f"  建议放弃: {rec_dist.get('discard', 0)}")
    
    # 应用统计
    app_stats = report.get("application_stats", {})
    click.echo(f"\n应用统计:")
    click.echo(f"  总应用: {app_stats.get('total', 0)}")
    if app_stats.get('total', 0) > 0:
        click.echo(f"  成功: {app_stats.get('success', 0)}")
        click.echo(f"  失败: {app_stats.get('failed', 0)}")
        click.echo(f"  成功率: {app_stats.get('success_rate', 0):.1%}")
    
    # 目标进度
    goals = report.get("goals", {})
    click.echo(f"\n目标进度:")
    click.echo(f"  总体进度: {goals.get('overall_progress', 0):.1f}%")
    goal_details = goals.get('goal_details', {})
    for name, detail in goal_details.items():
        progress = detail.get('progress', 0)
        bar = '█' * int(progress / 10) + '░' * (10 - int(progress / 10))
        click.echo(f"  {name}: [{bar}] {progress:.1f}%")


@evolution_cli.command(name="evaluate")
@click.argument('idea')
def evaluate_idea(idea):
    """评估一个想法"""
    evaluator = loop.evaluator if 'loop' in dir() else EvolutionFeedbackLoop().evaluator
    
    result = evaluator.evaluate(idea)
    
    click.echo(f"\n🧠 想法评估结果")
    click.echo("=" * 60)
    click.echo(f"想法: {idea}")
    click.echo(f"\n综合得分: {result.overall_score:.1f}/100")
    click.echo(f"置信度: {result.confidence:.0%}")
    click.echo(f"建议: {result.recommendation}")
    click.echo(f"估算投入: {result.estimated_effort}")
    click.echo(f"估算影响: {result.estimated_impact}")
    
    click.echo(f"\n详细评分:")
    for metric, score in result.scores.items():
        bar = '█' * int(score / 10) + '░' * (10 - int(score / 10))
        click.echo(f"  {metric}: [{bar}] {score:.1f}")
    
    click.echo(f"\n风险:")
    for risk in result.risks:
        click.echo(f"  - {risk}")


if __name__ == "__main__":
    evolution_cli()
