#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行记录自动复盘工具
核心功能：自动拉取指定时间范围内所有任务执行日志，统计工具调用成功率、失败场景、耗时分布，自动识别高频工具缺口
输入要求：时间范围（默认近3个月）、任务类型过滤条件、统计维度配置
输出要求：结构化工具缺口统计报告、高频缺失场景TOP列表、工具需求优先级排名
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import logging
from src.utils.logger import setup_logger

# 配置日志
logger = setup_logger(name="TaskExecutionReview")

class TaskExecutionReviewTool:
    def __init__(self, log_data_path: str = "./data/near_3month_runtime_data.json"):
        """
        初始化复盘工具
        :param log_data_path: 任务执行日志数据文件路径，默认使用近3个月运行数据文件
        """
        self.log_data_path = log_data_path
        self.raw_data = None
        self._load_log_data()
    
    def _load_log_data(self) -> None:
        """
        加载原始日志数据
        """
        try:
            if not os.path.exists(self.log_data_path):
                raise FileNotFoundError(f"日志数据文件不存在: {self.log_data_path}")
            with open(self.log_data_path, 'r', encoding='utf-8') as f:
                self.raw_data = json.load(f)
            logger.info(f"成功加载日志数据，共包含 {len(self.raw_data.get('recent_interactions', []))} 条交互记录")
        except Exception as e:
            logger.error(f"加载日志数据失败: {str(e)}")
            raise
    
    def _filter_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        按时间范围过滤交互记录
        :param start_time: 统计开始时间
        :param end_time: 统计结束时间
        :return: 过滤后的交互记录列表
        """
        filtered_records = []
        for record in self.raw_data.get('recent_interactions', []):
            try:
                record_time = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                if start_time <= record_time <= end_time:
                    filtered_records.append(record)
            except Exception as e:
                logger.warning(f"解析记录时间失败 {record.get('timestamp')}: {str(e)}，跳过该记录")
        return filtered_records
    
    def _filter_by_task_type(self, records: List[Dict], task_type: Optional[str] = None) -> List[Dict]:
        """
        按任务类型过滤记录
        :param records: 待过滤的记录列表
        :param task_type: 任务类型，None表示不过滤
        :return: 过滤后的记录列表
        """
        if not task_type:
            return records
        filtered = [r for r in records if r.get('instruction', '').strip() == task_type.strip()]
        return filtered
    
    def _calculate_tool_usage_stats(self, records: List[Dict]) -> Dict:
        """
        计算工具使用统计数据
        :param records: 交互记录列表
        :return: 工具使用统计字典
        """
        stats = {
            'total_calls': 0,
            'success_calls': 0,
            'failed_calls': 0,
            'success_rate': 0.0,
            'tool_usage_counts': defaultdict(int),
            'failed_scenarios': defaultdict(int),
            'tool_gap_scenarios': defaultdict(int)
        }
        
        # 定义工具调用失败关键字
        failed_keywords = ['失败', '错误', '异常', '无法执行', '不支持', '缺少', '无此工具', '功能不足']
        # 定义工具缺口关键字
        gap_keywords = ['需要', '想要', '希望', '能不能', '有没有', '缺少', '找不到', '没有']
        
        for record in records:
            stats['total_calls'] += 1
            output = record.get('output', '').lower()
            input_text = record.get('input', '').lower()
            
            # 判断是否调用失败
            is_failed = any(k in output for k in failed_keywords)
            if is_failed:
                stats['failed_calls'] += 1
                # 统计失败场景
                for kw in failed_keywords:
                    if kw in output:
                        stats['failed_scenarios'][kw] += 1
                        break
            else:
                stats['success_calls'] += 1
            
            # 统计工具缺口场景
            if any(k in input_text for k in gap_keywords) and '工具' in input_text:
                stats['tool_gap_scenarios'][input_text[:50]] += 1  # 截取前50字符作为场景标识
        
        # 计算成功率
        if stats['total_calls'] > 0:
            stats['success_rate'] = round(stats['success_calls'] / stats['total_calls'], 4) * 100
        
        return stats
    
    def _calculate_time_distribution(self, records: List[Dict]) -> Dict:
        """
        计算任务耗时分布（模拟耗时计算，实际可从日志中提取耗时字段）
        :param records: 交互记录列表
        :return: 耗时分布统计字典
        """
        distribution = {
            '0-1s': 0,
            '1-3s': 0,
            '3-5s': 0,
            '5-10s': 0,
            '10s+': 0
        }
        # 这里模拟耗时，实际场景应该从日志中获取真实耗时数据
        import random
        for _ in records:
            cost = random.uniform(0, 15)
            if cost < 1:
                distribution['0-1s'] += 1
            elif cost < 3:
                distribution['1-3s'] += 1
            elif cost < 5:
                distribution['3-5s'] += 1
            elif cost < 10:
                distribution['5-10s'] += 1
            else:
                distribution['10s+'] += 1
        return distribution
    
    def _generate_priority_ranking(self, gap_scenarios: Dict) -> List[Dict]:
        """
        生成工具需求优先级排名
        :param gap_scenarios: 工具缺口场景统计字典
        :return: 优先级排序列表
        """
        sorted_gaps = sorted(gap_scenarios.items(), key=lambda x: x[1], reverse=True)
        ranking = []
        for idx, (scenario, count) in enumerate(sorted_gaps, 1):
            priority = 'P0' if count >= 5 else 'P1' if count >= 3 else 'P2'
            ranking.append({
                'rank': idx,
                'scenario': scenario,
                'occurrence_count': count,
                'priority': priority
            })
        return ranking
    
    def run_review(self, 
                  start_time: Optional[str] = None, 
                  end_time: Optional[str] = None, 
                  task_type: Optional[str] = None,
                  top_n: int = 10) -> Dict:
        """
        执行任务复盘分析
        :param start_time: 统计开始时间，格式：YYYY-MM-DD HH:MM:SS，默认是3个月前
        :param end_time: 统计结束时间，格式：YYYY-MM-DD HH:MM:SS，默认是当前时间
        :param task_type: 任务类型过滤，None表示不过滤
        :param top_n: 高频缺口场景返回数量，默认10个
        :return: 完整的复盘分析报告
        """
        try:
            # 处理时间参数
            if not end_time:
                end_time_obj = datetime.now()
            else:
                end_time_obj = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
            
            if not start_time:
                start_time_obj = end_time_obj - timedelta(days=90)  # 默认近3个月
            else:
                start_time_obj = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            
            logger.info(f"开始复盘分析，时间范围：{start_time_obj.strftime('%Y-%m-%d %H:%M:%S')} 至 {end_time_obj.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 过滤记录
            filtered_records = self._filter_by_time_range(start_time_obj, end_time_obj)
            if task_type:
                filtered_records = self._filter_by_task_type(filtered_records, task_type)
            
            if not filtered_records:
                logger.warning("指定条件下没有匹配的记录")
                return {
                    'status': 'success',
                    'message': '没有匹配的记录',
                    'data': {}
                }
            
            # 计算各项统计数据
            usage_stats = self._calculate_tool_usage_stats(filtered_records)
            time_distribution = self._calculate_time_distribution(filtered_records)
            priority_ranking = self._generate_priority_ranking(usage_stats['tool_gap_scenarios'])
            top_gap_scenarios = priority_ranking[:top_n]
            
            # 组装返回结果
            report = {
                'status': 'success',
                'summary': {
                    'time_range': {
                        'start': start_time_obj.strftime('%Y-%m-%d %H:%M:%S'),
                        'end': end_time_obj.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'total_records': len(filtered_records),
                    'task_type_filter': task_type or '全部'
                },
                'tool_usage_stats': usage_stats,
                'time_cost_distribution': time_distribution,
                'top_gap_scenarios': top_gap_scenarios,
                'full_priority_ranking': priority_ranking
            }
            
            logger.info("复盘分析完成")
            return report
        
        except Exception as e:
            logger.error(f"复盘分析失败: {str(e)}")
            return {
                'status': 'failed',
                'message': f"复盘分析失败: {str(e)}",
                'data': {}
            }

# 对外暴露的工具调用函数
def task_execution_review(start_time: Optional[str] = None, 
                         end_time: Optional[str] = None, 
                         task_type: Optional[str] = None,
                         top_n: int = 10,
                         log_data_path: str = "./data/near_3month_runtime_data.json") -> Dict:
    """
    任务执行记录自动复盘工具对外接口
    :param start_time: 统计开始时间，格式：YYYY-MM-DD HH:MM:SS，默认是3个月前
    :param end_time: 统计结束时间，格式：YYYY-MM-DD HH:MM:SS，默认是当前时间
    :param task_type: 任务类型过滤，None表示不过滤
    :param top_n: 高频缺口场景返回数量，默认10个
    :param log_data_path: 日志数据文件路径，默认使用近3个月运行数据文件
    :return: 复盘分析报告
    """
    tool = TaskExecutionReviewTool(log_data_path)
    return tool.run_review(start_time, end_time, task_type, top_n)

if __name__ == "__main__":
    # 示例运行
    report = task_execution_review()
    print(json.dumps(report, ensure_ascii=False, indent=2))