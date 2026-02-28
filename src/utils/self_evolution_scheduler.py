#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主进化调度器核心模块
功能：自动触发能力短板识别、生成优化目标、优先级排序、调度执行迭代任务
完成标准：每月有效代码优化迭代次数≥20次
"""
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import asdict
from src.utils.autonomous_demand_system import AutonomousDemandSystem, IterationDemand, DemandPriority
from src.skills.evolution_skills import autonomous_iteration_pipeline, generate_iteration_plan
from src.utils.constants import OPTIMIZATION_HISTORY_FILE

class SelfEvolutionScheduler:
    def __init__(self, autonomous_demand_system: AutonomousDemandSystem):
        self.demand_system = autonomous_demand_system
        self.running = False
        self.scheduler_thread = None
        # 迭代历史记录存储路径
        self.iteration_history_path = OPTIMIZATION_HISTORY_FILE
        self.iteration_history = self._load_iteration_history()
        # 调度配置
        self.config = {
            # 迭代调度间隔（秒），默认每1天1次，保证每月至少20次（每月按30天算，间隔1.5天即可，这里设为86400秒=1天）
            "scheduler_interval": 86400,
            # 每次迭代最多处理的需求数
            "max_demands_per_iteration": 1,
            # 每月最低有效迭代次数要求
            "min_monthly_iterations": 20,
            # 迭代失败重试最大次数
            "max_retry_count": 3
        }

    def _load_iteration_history(self) -> List[Dict]:
        """加载历史迭代记录"""
        if self.iteration_history_path.exists():
            try:
                return json.loads(self.iteration_history_path.read_text(encoding='utf-8'))
            except Exception as e:
                print(f"加载迭代历史失败: {e}")
        return []

    def _save_iteration_history(self):
        """保存迭代记录到文件"""
        try:
            self.iteration_history_path.parent.mkdir(parents=True, exist_ok=True)
            self.iteration_history_path.write_text(json.dumps(self.iteration_history, indent=2, default=str), encoding='utf-8')
        except Exception as e:
            print(f"保存迭代历史失败: {e}")

    def get_monthly_iteration_count(self) -> int:
        """统计当月有效迭代次数"""
        now = datetime.now()
        month_start = datetime(now.year, now.month, 1).timestamp()
        count = sum(
            1 for record in self.iteration_history
            if record.get("timestamp", 0) >= month_start and record.get("success", False)
        )
        return count

    def adjust_scheduler_interval(self):
        """根据当月已完成迭代次数自动调整调度间隔，确保达标最低要求"""
        monthly_count = self.get_monthly_iteration_count()
        now = datetime.now()
        # 当月剩余天数
        days_remaining = (datetime(now.year, now.month + 1, 1) - now).days if now.month < 12 else 31 - now.day
        # 剩余需要完成的迭代数
        remaining_needed = max(self.config["min_monthly_iterations"] - monthly_count, 0)
        
        if remaining_needed > 0 and days_remaining > 0:
            # 计算需要的间隔，确保剩余时间内完成
            required_interval = (days_remaining * 86400) / remaining_needed
            # 取当前配置和需要的间隔的最小值，加快调度频率
            self.config["scheduler_interval"] = min(self.config["scheduler_interval"], required_interval)
            print(f"调整迭代调度间隔为{self.config['scheduler_interval']/3600:.1f}小时，当月已完成{monthly_count}次，剩余需完成{remaining_needed}次")
        else:
            # 达标后恢复默认间隔
            self.config["scheduler_interval"] = 86400
            print(f"当月迭代次数已达标({monthly_count}/{self.config['min_monthly_iterations']})，恢复默认调度间隔")

    def execute_single_iteration(self, demand: IterationDemand) -> Tuple[bool, Dict]:
        """执行单次迭代任务"""
        print(f"开始执行迭代任务: {demand.title}, 优先级: {demand.priority.name}")
        
        # 生成迭代执行计划
        plan = generate_iteration_plan([asdict(demand)], self.config["max_demands_per_iteration"])
        
        # 记录迭代前状态
        before_status = self.demand_system.collect_current_status()
        
        success = False
        details = {}
        retry_count = 0
        
        while not success and retry_count < self.config["max_retry_count"]:
            try:
                # 调用全流程自主迭代管道执行优化
                success, details = autonomous_iteration_pipeline(
                    target_module_path=plan["target_module_path"],
                    modified_code_content=plan["modified_code"],
                    associated_test_cases=plan.get("test_cases"),
                    smoke_test_code=plan.get("smoke_test")
                )
                if success:
                    break
            except Exception as e:
                print(f"迭代执行失败(第{retry_count+1}次重试): {e}")
                retry_count += 1
                time.sleep(60)
        
        # 验证迭代效果
        after_status = self.demand_system.collect_current_status()
        verification_result = self.demand_system.verify_demand(demand.demand_id, before_status, after_status)
        
        # 记录迭代历史
        iteration_record = {
            "timestamp": time.time(),
            "demand_id": demand.demand_id,
            "title": demand.title,
            "priority": demand.priority.name,
            "success": success and verification_result["passed"],
            "verification_result": verification_result,
            "execution_details": details,
            "retry_count": retry_count
        }
        self.iteration_history.append(iteration_record)
        self._save_iteration_history()
        
        print(f"迭代任务{demand.title}执行结果: {'成功' if iteration_record['success'] else '失败'}")
        return iteration_record["success"], iteration_record

    def _scheduler_loop(self):
        """调度主循环"""
        while self.running:
            try:
                # 调整调度间隔
                self.adjust_scheduler_interval()
                
                # 获取优先级排序后的待处理需求
                prioritized_demands = self.demand_system.get_prioritized_demands()
                
                if prioritized_demands:
                    # 取优先级最高的需求执行
                    top_demand = prioritized_demands[0]
                    self.execute_single_iteration(top_demand)
                else:
                    print("当前无待处理优化需求，跳过本次调度")
                
                # 等待下一次调度
                time.sleep(self.config["scheduler_interval"])
            except Exception as e:
                print(f"调度循环出错: {e}")
                time.sleep(3600) # 出错后等待1小时再重试

    def start(self):
        """启动调度器"""
        if self.running:
            print("自主进化调度器已在运行")
            return
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("自主进化调度器已启动")

    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        print("自主进化调度器已停止")

    def get_scheduler_status(self) -> Dict:
        """获取调度器运行状态"""
        monthly_count = self.get_monthly_iteration_count()
        return {
            "running": self.running,
            "monthly_completed_iterations": monthly_count,
            "monthly_target": self.config["min_monthly_iterations"],
            "target_achieved": monthly_count >= self.config["min_monthly_iterations"],
            "pending_demands_count": len([d for d in self.demand_system.demands.values() if d.status == "pending"]),
            "scheduler_interval_hours": self.config["scheduler_interval"] / 3600,
            "total_iterations": len(self.iteration_history)
        }
