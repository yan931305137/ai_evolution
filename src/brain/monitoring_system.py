"""
Brain Monitoring System - Brain运行监控指标系统

提供全面的运行时监控和性能指标收集能力

功能：
1. 性能指标监控（响应时间、内存使用等）
2. 情感状态追踪
3. 记忆使用统计
4. 决策质量分析
5. 健康检查
6. 指标导出（支持Prometheus格式）
"""
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import json


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"      # 计数器（只增不减）
    GAUGE = "gauge"          # 仪表盘（可增可减）
    HISTOGRAM = "histogram"  # 直方图（分布统计）
    SUMMARY = "summary"      # 摘要（分位数统计）


@dataclass
class Metric:
    """指标数据点"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class TimeSeries:
    """时间序列数据"""
    metric_name: str
    data: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add(self, value: float, labels: Dict[str, str] = None):
        """添加数据点"""
        self.data.append({
            "value": value,
            "labels": labels or {},
            "timestamp": datetime.now()
        })
    
    def get_recent(self, n: int = 100) -> List[Dict]:
        """获取最近n个数据点"""
        return list(self.data)[-n:]
    
    def get_average(self, window_seconds: int = 60) -> float:
        """获取时间窗口内的平均值"""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        values = [
            d["value"] for d in self.data 
            if d["timestamp"] > cutoff
        ]
        return sum(values) / len(values) if values else 0.0


class BrainMonitor:
    """
    Brain监控器
    
    收集和报告Brain运行时的各种指标
    """
    
    def __init__(self, brain_reference=None, collection_interval: int = 10):
        """
        初始化监控器
        
        Args:
            brain_reference: Brain实例引用
            collection_interval: 指标收集间隔（秒）
        """
        self.brain = brain_reference
        self.collection_interval = collection_interval
        
        # 指标存储
        self.metrics: Dict[str, Metric] = {}
        self.time_series: Dict[str, TimeSeries] = {}
        
        # 性能追踪
        self.performance_stats = {
            "response_times": deque(maxlen=1000),
            "memory_usage": deque(maxlen=100),
            "cpu_usage": deque(maxlen=100)
        }
        
        # 事件日志
        self.event_log: deque = deque(maxlen=1000)
        
        # 告警规则
        self.alert_rules: List[Dict] = []
        self.alert_handlers: List[Callable] = []
        
        # 运行状态
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 初始化系统指标
        self._init_system_metrics()
    
    def _init_system_metrics(self):
        """初始化系统指标"""
        process = psutil.Process()
        
        self.metrics["system_cpu_percent"] = Metric(
            name="system_cpu_percent",
            value=psutil.cpu_percent(),
            metric_type=MetricType.GAUGE
        )
        
        self.metrics["system_memory_percent"] = Metric(
            name="system_memory_percent",
            value=psutil.virtual_memory().percent,
            metric_type=MetricType.GAUGE
        )
        
        self.metrics["process_memory_mb"] = Metric(
            name="process_memory_mb",
            value=process.memory_info().rss / 1024 / 1024,
            metric_type=MetricType.GAUGE
        )
    
    def start(self):
        """启动监控"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        print("📊 Brain监控已启动")
    
    def stop(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("📊 Brain监控已停止")
    
    def _monitoring_loop(self):
        """监控主循环"""
        while self.is_running:
            try:
                self._collect_metrics()
                self._check_alerts()
                time.sleep(self.collection_interval)
            except Exception as e:
                self.log_event("monitor_error", {"error": str(e)})
    
    def _collect_metrics(self):
        """收集指标"""
        if not self.brain:
            return
        
        # 系统资源指标
        self._update_system_metrics()
        
        # Brain特定指标
        self._update_brain_metrics()
        
        # 性能指标
        self._update_performance_metrics()
    
    def _update_system_metrics(self):
        """更新系统指标"""
        # CPU使用率
        cpu_percent = psutil.cpu_percent()
        self._record_metric("system_cpu_percent", cpu_percent, MetricType.GAUGE)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        self._record_metric("system_memory_percent", memory.percent, MetricType.GAUGE)
        
        # 进程内存
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        self._record_metric("process_memory_mb", mem_mb, MetricType.GAUGE)
        
        self.performance_stats["memory_usage"].append(mem_mb)
    
    def _update_brain_metrics(self):
        """更新Brain指标"""
        try:
            # 情感状态指标
            if hasattr(self.brain, 'emotion') and self.brain.emotion:
                emotion = self.brain.emotion.current_emotion
                self._record_metric("brain_emotion_valence", emotion.valence, MetricType.GAUGE)
                self._record_metric("brain_emotion_arousal", emotion.arousal, MetricType.GAUGE)
            
            # 发育阶段指标
            if hasattr(self.brain, 'developmental') and self.brain.developmental:
                stage_value = self._stage_to_number(self.brain.developmental.stage)
                self._record_metric("brain_developmental_stage", stage_value, MetricType.GAUGE)
                
                age = self.brain.developmental.age_equivalent
                self._record_metric("brain_age_equivalent", age, MetricType.GAUGE)
            
            # 记忆统计
            if hasattr(self.brain, 'use_persistent_memory') and self.brain.use_persistent_memory:
                if hasattr(self.brain, 'memory') and hasattr(self.brain.memory, 'get_memory_stats'):
                    stats = self.brain.memory.get_memory_stats()
                    if stats:
                        self._record_metric("brain_memory_count", stats.get("memory_count", 0), MetricType.GAUGE)
            
            # 社交关系数量
            if hasattr(self.brain, 'social') and self.brain.social:
                relation_count = len(self.brain.social.relationships)
                self._record_metric("brain_relationship_count", relation_count, MetricType.GAUGE)
            
            # 生理需求指标
            if hasattr(self.brain, 'homeostasis') and self.brain.homeostasis:
                for need, level in self.brain.homeostasis.needs.items():
                    self._record_metric(
                        f"brain_need_{need.value}", 
                        level, 
                        MetricType.GAUGE
                    )
            
            # 叙事自我长度
            if hasattr(self.brain, 'life_narrative'):
                narrative_len = len(self.brain.life_narrative)
                self._record_metric("brain_narrative_length", narrative_len, MetricType.COUNTER)
            
            # 交互次数
            if hasattr(self.brain, 'interaction_count'):
                self._record_metric(
                    "brain_total_interactions", 
                    self.brain.interaction_count, 
                    MetricType.COUNTER
                )
                
        except Exception as e:
            self.log_event("metrics_collection_error", {"error": str(e)})
    
    def _update_performance_metrics(self):
        """更新性能指标"""
        # 计算平均响应时间
        if self.performance_stats["response_times"]:
            avg_time = sum(self.performance_stats["response_times"]) / len(self.performance_stats["response_times"])
            self._record_metric("brain_avg_response_time_ms", avg_time, MetricType.GAUGE)
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, labels: Dict = None):
        """记录指标"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )
        self.metrics[name] = metric
        
        # 更新时间序列
        if name not in self.time_series:
            self.time_series[name] = TimeSeries(metric_name=name)
        self.time_series[name].add(value, labels)
    
    def _stage_to_number(self, stage) -> int:
        """将发育阶段转换为数字"""
        stage_map = {
            "INFANT": 0,
            "TODDLER": 1,
            "CHILD": 2,
            "ADOLESCENT": 3,
            "ADULT": 4
        }
        return stage_map.get(stage.name if hasattr(stage, 'name') else str(stage), -1)
    
    def record_response_time(self, duration_ms: float):
        """记录响应时间"""
        self.performance_stats["response_times"].append(duration_ms)
        self._record_metric("brain_response_time_ms", duration_ms, MetricType.HISTOGRAM)
    
    def record_decision(self, action: str, confidence: float, success: bool = True):
        """记录决策"""
        self._record_metric(
            "brain_decision_count", 
            1, 
            MetricType.COUNTER,
            labels={"action": action, "success": str(success)}
        )
        self._record_metric("brain_decision_confidence", confidence, MetricType.GAUGE)
    
    def log_event(self, event_type: str, details: Dict):
        """记录事件"""
        event = {
            "type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.event_log.append(event)
    
    def add_alert_rule(self, metric_name: str, threshold: float, 
                      comparison: str = ">", handler: Callable = None):
        """
        添加告警规则
        
        Args:
            metric_name: 指标名称
            threshold: 阈值
            comparison: 比较运算符（>, <, >=, <=, ==）
            handler: 告警处理函数
        """
        rule = {
            "metric_name": metric_name,
            "threshold": threshold,
            "comparison": comparison,
            "handler": handler,
            "last_alert": None
        }
        self.alert_rules.append(rule)
    
    def _check_alerts(self):
        """检查告警"""
        for rule in self.alert_rules:
            metric = self.metrics.get(rule["metric_name"])
            if not metric:
                continue
            
            value = metric.value
            threshold = rule["threshold"]
            comparison = rule["comparison"]
            
            triggered = False
            if comparison == ">" and value > threshold:
                triggered = True
            elif comparison == "<" and value < threshold:
                triggered = True
            elif comparison == ">=" and value >= threshold:
                triggered = True
            elif comparison == "<=" and value <= threshold:
                triggered = True
            elif comparison == "==" and value == threshold:
                triggered = True
            
            if triggered:
                # 避免频繁告警（至少间隔5分钟）
                last_alert = rule.get("last_alert")
                if last_alert and (datetime.now() - last_alert) < timedelta(minutes=5):
                    continue
                
                rule["last_alert"] = datetime.now()
                
                alert_info = {
                    "metric": rule["metric_name"],
                    "value": value,
                    "threshold": threshold,
                    "comparison": comparison,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 调用处理器
                if rule["handler"]:
                    try:
                        rule["handler"](alert_info)
                    except Exception as e:
                        print(f"Alert handler error: {e}")
                
                # 记录事件
                self.log_event("alert_triggered", alert_info)
    
    def get_metrics_summary(self) -> Dict:
        """获取指标摘要"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_metrics": len(self.metrics),
            "metrics": {name: metric.to_dict() for name, metric in self.metrics.items()},
            "recent_events": list(self.event_log)[-10:],
            "performance_summary": {
                "avg_response_time": self._get_avg_response_time(),
                "avg_memory_usage": self._get_avg_memory_usage(),
                "total_interactions": self._get_total_interactions()
            }
        }
    
    def _get_avg_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.performance_stats["response_times"]:
            return 0.0
        return sum(self.performance_stats["response_times"]) / len(self.performance_stats["response_times"])
    
    def _get_avg_memory_usage(self) -> float:
        """获取平均内存使用"""
        if not self.performance_stats["memory_usage"]:
            return 0.0
        return sum(self.performance_stats["memory_usage"]) / len(self.performance_stats["memory_usage"])
    
    def _get_total_interactions(self) -> int:
        """获取总交互数"""
        if self.brain and hasattr(self.brain, 'interaction_count'):
            return self.brain.interaction_count
        return 0
    
    def export_prometheus_format(self) -> str:
        """导出Prometheus格式的指标"""
        lines = []
        
        for name, metric in self.metrics.items():
            # 指标类型
            lines.append(f"# TYPE {name} {metric.metric_type.value}")
            
            # 指标值
            labels_str = ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
            if labels_str:
                lines.append(f"{name}{{{labels_str}}} {metric.value}")
            else:
                lines.append(f"{name} {metric.value}")
        
        return "\n".join(lines)
    
    def get_health_status(self) -> Dict:
        """获取健康状态"""
        checks = {
            "brain_initialized": self.brain is not None,
            "monitor_running": self.is_running,
            "memory_usage_ok": self.metrics.get("process_memory_mb", Metric("", 0, MetricType.GAUGE)).value < 1000,
            "cpu_usage_ok": self.metrics.get("system_cpu_percent", Metric("", 0, MetricType.GAUGE)).value < 80,
            "response_time_ok": self._get_avg_response_time() < 5000  # 5秒
        }
        
        overall_health = "healthy" if all(checks.values()) else "degraded" if checks["brain_initialized"] else "unhealthy"
        
        return {
            "status": overall_health,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    
    def create_dashboard_data(self) -> Dict:
        """创建仪表盘数据"""
        return {
            "real_time_metrics": self.get_metrics_summary(),
            "emotion_trend": self._get_emotion_trend(),
            "performance_trend": self._get_performance_trend(),
            "recent_events": list(self.event_log)[-20:],
            "health_status": self.get_health_status()
        }
    
    def _get_emotion_trend(self) -> List[Dict]:
        """获取情感趋势"""
        if "brain_emotion_valence" in self.time_series:
            return self.time_series["brain_emotion_valence"].get_recent(50)
        return []
    
    def _get_performance_trend(self) -> List[Dict]:
        """获取性能趋势"""
        if "brain_response_time_ms" in self.time_series:
            return self.time_series["brain_response_time_ms"].get_recent(50)
        return []


# 便捷函数
def create_monitor(brain, auto_start: bool = True) -> BrainMonitor:
    """
    创建并启动监控器
    
    Args:
        brain: Brain实例
        auto_start: 是否自动启动
        
    Returns:
        BrainMonitor实例
    """
    monitor = BrainMonitor(brain_reference=brain)
    
    # 添加默认告警规则
    monitor.add_alert_rule(
        metric_name="process_memory_mb",
        threshold=1000,
        comparison=">",
        handler=lambda alert: print(f"⚠️ 内存告警: {alert['value']:.1f}MB")
    )
    
    monitor.add_alert_rule(
        metric_name="system_cpu_percent",
        threshold=90,
        comparison=">",
        handler=lambda alert: print(f"⚠️ CPU告警: {alert['value']:.1f}%")
    )
    
    if auto_start:
        monitor.start()
    
    return monitor
