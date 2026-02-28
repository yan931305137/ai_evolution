"""
自主需求生成与评估体系核心模块
包含四个核心子模块：运行状态感知、能力短板识别、需求优先级排序、迭代效果验证
"""
import time
import json
import os
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from src.utils.constants import MONITOR_STATUS_FILE


class DemandPriority(Enum):
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class IterationDemand:
    demand_id: str
    title: str
    description: str
    root_cause: str
    priority: DemandPriority
    estimated_cost: int
    expected_benefit: float
    related_capability: Optional[str] = None
    created_time: float = field(default_factory=time.time)
    status: str = "pending"
    verification_result: Optional[Dict] = None


@dataclass
class RuntimeStatus:
    timestamp: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    process_uptime: float
    total_task_count: int
    success_task_count: int
    task_success_rate: float
    average_task_duration: float
    error_count: int
    recent_errors: List[Dict]
    capability_performance: Dict[str, Dict]
    user_satisfaction_score: float


class AutonomousDemandSystem:
    def __init__(self, self_awareness_system, database):
        self.self_awareness = self_awareness_system
        self.db = database
        self.running = False
        self.status_thread = None
        
        self.config = {
            "task_success_rate_threshold": 0.8,
            "capability_confidence_threshold": 60,
            "cpu_usage_threshold": 80,
            "memory_usage_threshold": 85,
            "demand_accuracy_target": 0.95,
            "min_observation_count": 3
        }
        
        self.status_history: List[RuntimeStatus] = []
        self.max_history = 1000
        self.demands: Dict[str, IterationDemand] = {}
        self.problem_counts: Dict[str, int] = {}
        self.verification_records: List[Dict] = []

    def start(self):
        if self.running:
            return
        self.running = True
        self.status_thread = threading.Thread(target=self._collect_status_loop, daemon=True)
        self.status_thread.start()

    def stop(self):
        self.running = False
        if self.status_thread:
            self.status_thread.join()

    # 运行状态感知模块
    def _collect_status_loop(self):
        # Initial collection immediately upon start
        try:
             status = self.collect_current_status()
             self._save_monitor_status(status)
             self.status_history.append(status)
             self.identify_shortcomings(status)
        except Exception as e:
            print(f"Initial status collection failed: {e}")

        while self.running:
            time.sleep(10) # Reduced from 300s to 10s for better responsiveness
            try:
                status = self.collect_current_status()
                self.status_history.append(status)
                if len(self.status_history) > self.max_history:
                    self.status_history.pop(0)
                
                self._save_monitor_status(status)
                self.identify_shortcomings(status)
            except Exception as e:
                print(f"Status loop error: {e}")
                pass
            
    def _save_monitor_status(self, status: RuntimeStatus):
        """Helper to save status to JSON for dashboard"""
        try:
            status_dict = asdict(status)
            # Convert un-serializable types if any (e.g., set)
            # Write to a fixed location for the dashboard to read
            monitor_path = MONITOR_STATUS_FILE
            monitor_path.parent.mkdir(parents=True, exist_ok=True)
            monitor_path.write_text(json.dumps(status_dict, indent=2, default=str), encoding='utf-8')
        except Exception as e:
            print(f"Error saving monitor status: {e}")

    def collect_current_status(self) -> RuntimeStatus:
        process = psutil.Process(os.getpid())
        cpu = process.cpu_percent(interval=0.5)
        memory = process.memory_info().rss / psutil.virtual_memory().total * 100
        disk = psutil.disk_usage('/').percent
        uptime = time.time() - process.create_time()

        recent_tasks = self.db.query("SELECT * FROM tasks WHERE created_at > ?", (time.time() - 86400,)) or []
        total_tasks = len(recent_tasks)
        success_tasks = sum(1 for t in recent_tasks if t.get("success", 0))
        success_rate = success_tasks / total_tasks if total_tasks > 0 else 1.0
        avg_duration = sum(t.get("duration", 0) for t in recent_tasks) / total_tasks if total_tasks > 0 else 0
        recent_errors = [t for t in recent_tasks if not t.get("success", 0)][-10:]

        cap_perf = {}
        if hasattr(self.self_awareness, 'capabilities'):
            for name, cap in self.self_awareness.capabilities.items():
                cap_perf[name] = {
                    "confidence": cap.confidence,
                    "success_rate": cap.success_rate,
                    "usage_count": cap.usage_count
                }

        recent_feedback = self.db.query("SELECT * FROM feedback WHERE created_at > ?", (time.time() - 86400,)) or []
        satisfaction = sum(f.get("score", 5) for f in recent_feedback) / len(recent_feedback) * 10 if recent_feedback else 75

        return RuntimeStatus(
            timestamp=time.time(),
            cpu_usage=cpu,
            memory_usage=memory,
            disk_usage=disk,
            process_uptime=uptime,
            total_task_count=total_tasks,
            success_task_count=success_tasks,
            task_success_rate=success_rate,
            average_task_duration=avg_duration,
            error_count=len(recent_errors),
            recent_errors=recent_errors,
            capability_performance=cap_perf,
            user_satisfaction_score=satisfaction
        )

    # 能力短板识别模块
    def identify_shortcomings(self, status: RuntimeStatus) -> List[str]:
        problems = []
        if status.cpu_usage > self.config["cpu_usage_threshold"]:
            problems.append("performance:high_cpu")
        if status.memory_usage > self.config["memory_usage_threshold"]:
            problems.append("performance:high_memory")
        if status.average_task_duration > 30:
            problems.append("performance:slow_response")

        for cap_name, perf in status.capability_performance.items():
            if perf.get("usage_count", 0) >= 5 and perf.get("confidence", 100) < self.config["capability_confidence_threshold"]:
                problems.append(f"capability:low_{cap_name}_confidence")
            if perf.get("usage_count", 0) >= 10 and perf.get("success_rate", 1) < self.config["task_success_rate_threshold"]:
                problems.append(f"capability:low_{cap_name}_success")

        if status.task_success_rate < self.config["task_success_rate_threshold"] and status.total_task_count >= 10:
            problems.append("task:low_success_rate")
        if status.error_count >= 5:
            problems.append("task:high_error_count")
        if status.user_satisfaction_score < 70:
            problems.append("experience:low_satisfaction")

        for problem in problems:
            self.problem_counts[problem] = self.problem_counts.get(problem, 0) + 1
            if self.problem_counts[problem] >= self.config["min_observation_count"]:
                existing = [d for d in self.demands.values() if d.root_cause == problem and d.status == "pending"]
                if not existing:
                    self.generate_demand(problem, status)
        return problems

    def generate_demand(self, problem: str, status: RuntimeStatus) -> IterationDemand:
        demand_id = f"demand_{int(time.time())}_{problem.replace(':', '_')}"
        problem_type, detail = problem.split(":", 1)
        cap_name = None

        if problem_type == "performance":
            if detail == "high_cpu":
                title = "优化CPU使用率"
                desc = f"CPU使用率{status.cpu_usage:.1f}%超过阈值"
                priority = DemandPriority.HIGH
                cost, benefit = 2, 85
            elif detail == "high_memory":
                title = "优化内存占用"
                desc = f"内存使用率{status.memory_usage:.1f}%超过阈值"
                priority = DemandPriority.HIGH
                cost, benefit = 2, 85
            else:
                title = "优化任务响应速度"
                desc = f"平均执行时间{status.average_task_duration:.1f}s超过阈值"
                priority = DemandPriority.MEDIUM
                cost, benefit = 3, 80
        elif problem_type == "capability":
            parts = detail.split("_")
            cap_name = '_'.join(parts[1:-1])
            if "success" in detail:
                title = f"提升{cap_name}能力成功率"
                desc = f"{cap_name}成功率{status.capability_performance[cap_name]['success_rate']:.2f}低于阈值"
            else:
                title = f"提升{cap_name}能力信心度"
                desc = f"{cap_name}信心度{status.capability_performance[cap_name]['confidence']:.1f}低于阈值"
            priority = DemandPriority.HIGH if cap_name in ["reasoning", "memory", "problem_solving"] else DemandPriority.MEDIUM
            cost, benefit = 3, 90
        elif problem_type == "task":
            title = "提升整体任务成功率" if detail == "low_success_rate" else "降低错误率"
            desc = f"任务成功率{status.task_success_rate:.2f}，错误数{status.error_count}"
            priority = DemandPriority.CRITICAL
            cost, benefit = 4, 95
        else:
            title = "提升用户满意度"
            desc = f"用户满意度{status.user_satisfaction_score:.1f}低于阈值"
            priority = DemandPriority.MEDIUM
            cost, benefit = 2, 80

        demand = IterationDemand(
            demand_id=demand_id, title=title, description=desc, root_cause=problem,
            priority=priority, estimated_cost=cost, expected_benefit=benefit,
            related_capability=cap_name
        )
        self.demands[demand_id] = demand
        return demand

    # 需求优先级排序模块
    def get_prioritized_demands(self) -> List[IterationDemand]:
        pending = [d for d in self.demands.values() if d.status == "pending"]
        def score(d):
            return d.priority.value * 20 * 0.4 + d.expected_benefit * 0.3 + (100 / max(d.estimated_cost, 1)) * 0.3
        pending.sort(key=score, reverse=True)
        return pending

    # 迭代效果验证模块
    def verify_demand(self, demand_id: str, before_status: RuntimeStatus, after_status: RuntimeStatus) -> Dict:
        demand = self.demands.get(demand_id)
        if not demand:
            return {"success": False, "error": "需求不存在"}
        result = {"demand_id": demand_id, "title": demand.title, "improvement": {}, "passed": False}
        problem = demand.root_cause

        if problem == "performance:high_cpu":
            imp = (before_status.cpu_usage - after_status.cpu_usage) / before_status.cpu_usage * 100
            result["improvement"]["cpu_reduction"] = imp
            result["passed"] = after_status.cpu_usage < 80 and imp >=10
        elif problem.startswith("capability:low_") and "success" in problem:
            cap = demand.related_capability
            before_rate = before_status.capability_performance[cap]["success_rate"]
            after_rate = after_status.capability_performance[cap]["success_rate"]
            imp = (after_rate - before_rate) / before_rate * 100
            result["improvement"]["success_rate_increase"] = imp
            result["passed"] = after_rate >= 0.8 and imp >=10
        else:
            result["passed"] = True

        demand.status = "completed" if result["passed"] else "failed"
        demand.verification_result = result
        self.verification_records.append(result)
        total = len(self.verification_records)
        passed = sum(1 for r in self.verification_records if r["passed"])
        result["overall_accuracy"] = passed / total if total else 1.0
        result["accuracy_target_met"] = result["overall_accuracy"] >= self.config["demand_accuracy_target"]
        return result
