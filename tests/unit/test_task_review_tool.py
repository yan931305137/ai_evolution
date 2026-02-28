#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行记录自动复盘工具测试用例
包含18个测试场景，覆盖功能点：时间范围过滤、任务类型过滤、统计计算、异常处理等
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from src.tools.task_review_tool import TaskExecutionReviewTool, task_execution_review

# 测试用临时数据文件路径
TEST_LOG_PATH = "./data/test_runtime_data.json"

@pytest.fixture(scope="module")
def test_log_data():
    """
    生成测试用的模拟日志数据
    """
    test_data = {
        "capability_success_rates": {},
        "recent_interactions": [
            # 模拟不同时间、不同类型、不同状态的记录
            {"id": 1, "instruction": "General Chat", "input": "你好", "output": "你好呀", "timestamp": "2026-02-01 10:00:00", "rating": 0, "feedback": None},
            {"id": 2, "instruction": "General Chat", "input": "需要文件整理工具", "output": "好的，我帮你整理", "timestamp": "2026-02-05 14:00:00", "rating": 0, "feedback": None},
            {"id": 3, "instruction": "Tool Call", "input": "调用list_files", "output": "执行成功，返回文件列表", "timestamp": "2026-02-10 09:30:00", "rating": 1, "feedback": None},
            {"id": 4, "instruction": "Tool Call", "input": "调用不存在的工具", "output": "错误：无此工具，无法执行", "timestamp": "2026-02-15 16:20:00", "rating": 0, "feedback": None},
            {"id": 5, "instruction": "General Chat", "input": "有没有代码生成工具", "output": "暂时没有这个功能", "timestamp": "2026-02-20 11:10:00", "rating": 0, "feedback": None},
            {"id": 6, "instruction": "Tool Call", "input": "调用read_file", "output": "读取文件失败，文件不存在", "timestamp": "2026-02-22 15:45:00", "rating": 0, "feedback": None},
            {"id": 7, "instruction": "General Chat", "input": "需要测试工具", "output": "好的，我帮你找", "timestamp": "2026-02-25 08:30:00", "rating": 1, "feedback": None},
            {"id": 8, "instruction": "Tool Call", "input": "调用write_file", "output": "写入文件成功", "timestamp": "2026-02-26 13:15:00", "rating": 1, "feedback": None},
            {"id": 9, "instruction": "General Chat", "input": "能不能开发个数据分析工具", "output": "我可以帮你生成需求", "timestamp": "2026-02-27 17:00:00", "rating": 1, "feedback": None},
            {"id": 10, "instruction": "Tool Call", "input": "调用run_command", "output": "执行异常，权限不足", "timestamp": "2026-02-28 10:00:00", "rating": 0, "feedback": None},
            {"id": 11, "instruction": "General Chat", "input": "需要图片处理工具", "output": "好的，我帮你查找", "timestamp": "2026-02-28 12:00:00", "rating": 1, "feedback": None},
            {"id": 12, "instruction": "Tool Call", "input": "调用clone_repo", "output": "克隆仓库成功", "timestamp": "2026-02-28 14:00:00", "rating": 1, "feedback": None},
            {"id": 13, "instruction": "General Chat", "input": "有没有视频生成工具", "output": "暂时不支持", "timestamp": "2026-02-28 16:00:00", "rating": 0, "feedback": None},
            {"id": 14, "instruction": "Tool Call", "input": "调用patch_code", "output": "修改代码成功", "timestamp": "2026-02-28 18:00:00", "rating": 1, "feedback": None},
            {"id": 15, "instruction": "General Chat", "input": "需要数据备份工具", "output": "我可以帮你开发", "timestamp": "2026-02-28 20:00:00", "rating": 1, "feedback": None},
            # 异常时间格式记录
            {"id": 16, "instruction": "General Chat", "input": "测试", "output": "测试", "timestamp": "2026/02/28", "rating": 0, "feedback": None},
        ]
    }
    # 写入测试数据文件
    with open(TEST_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    yield TEST_LOG_PATH
    # 测试完成后删除临时文件
    if os.path.exists(TEST_LOG_PATH):
        os.remove(TEST_LOG_PATH)

class TestTaskReviewTool:
    def test_init_success(self, test_log_data):
        """测试场景1：工具初始化成功"""
        tool = TaskExecutionReviewTool(test_log_data)
        assert tool.raw_data is not None
        assert len(tool.raw_data['recent_interactions']) == 16

    def test_init_file_not_exist(self):
        """测试场景2：初始化时日志文件不存在，抛出异常"""
        with pytest.raises(FileNotFoundError):
            TaskExecutionReviewTool("./data/not_exist_file.json")

    def test_filter_by_time_range_full_range(self, test_log_data):
        """测试场景3：时间范围过滤，全时间段匹配所有记录"""
        tool = TaskExecutionReviewTool(test_log_data)
        start = datetime(2026, 2, 1, 0, 0, 0)
        end = datetime(2026, 2, 28, 23, 59, 59)
        records = tool._filter_by_time_range(start, end)
        # 排除时间格式错误的1条，剩下15条
        assert len(records) == 15

    def test_filter_by_time_range_partial(self, test_log_data):
        """测试场景4：时间范围过滤，部分时间段匹配"""
        tool = TaskExecutionReviewTool(test_log_data)
        start = datetime(2026, 2, 20, 0, 0, 0)
        end = datetime(2026, 2, 28, 23, 59, 59)
        records = tool._filter_by_time_range(start, end)
        # 20号及以后的有效记录是11条（id5到id15）
        assert len(records) == 11

    def test_filter_by_time_range_no_match(self, test_log_data):
        """测试场景5：时间范围过滤，无匹配记录"""
        tool = TaskExecutionReviewTool(test_log_data)
        start = datetime(2025, 1, 1, 0, 0, 0)
        end = datetime(2025, 12, 31, 23, 59, 59)
        records = tool._filter_by_time_range(start, end)
        assert len(records) == 0

    def test_filter_by_task_type_all(self, test_log_data):
        """测试场景6：任务类型过滤，不过滤返回所有记录"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_task_type(tool.raw_data['recent_interactions'], None)
        assert len(records) == 16

    def test_filter_by_task_type_general_chat(self, test_log_data):
        """测试场景7：任务类型过滤，只返回General Chat类型"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_task_type(tool.raw_data['recent_interactions'], "General Chat")
        # 共有9条General Chat记录
        assert len(records) == 9

    def test_filter_by_task_type_tool_call(self, test_log_data):
        """测试场景8：任务类型过滤，只返回Tool Call类型"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_task_type(tool.raw_data['recent_interactions'], "Tool Call")
        # 共有7条Tool Call记录
        assert len(records) == 7

    def test_filter_by_task_type_no_match(self, test_log_data):
        """测试场景9：任务类型过滤，无匹配类型"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_task_type(tool.raw_data['recent_interactions'], "Not Exist Type")
        assert len(records) == 0

    def test_calculate_tool_usage_stats_success(self, test_log_data):
        """测试场景10：工具使用统计计算，成功率计算正确"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_time_range(datetime(2026,2,1), datetime(2026,2,28,23,59,59))
        stats = tool._calculate_tool_usage_stats(records)
        # 总调用15次，失败4次（id4,6,10,13），成功11次，成功率73.33%
        assert stats['total_calls'] == 15
        assert stats['success_calls'] == 11
        assert stats['failed_calls'] == 4
        assert stats['success_rate'] == round(11/15*100, 2)

    def test_calculate_tool_usage_stats_gap_recognition(self, test_log_data):
        """测试场景11：工具缺口识别正确"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_time_range(datetime(2026,2,1), datetime(2026,2,28,23,59,59))
        stats = tool._calculate_tool_usage_stats(records)
        # 共有7个工具缺口场景
        assert len(stats['tool_gap_scenarios']) == 7

    def test_calculate_time_distribution(self, test_log_data):
        """测试场景12：耗时分布计算正常"""
        tool = TaskExecutionReviewTool(test_log_data)
        records = tool._filter_by_time_range(datetime(2026,2,1), datetime(2026,2,28,23,59,59))
        distribution = tool._calculate_time_distribution(records)
        # 所有分布项加起来等于记录总数15
        total = sum(distribution.values())
        assert total == 15
        # 所有分布键都存在
        assert '0-1s' in distribution
        assert '1-3s' in distribution
        assert '3-5s' in distribution
        assert '5-10s' in distribution
        assert '10s+' in distribution

    def test_generate_priority_ranking(self, test_log_data):
        """测试场景13：优先级排名生成正确"""
        tool = TaskExecutionReviewTool(test_log_data)
        # 模拟缺口场景
        gaps = {
            "需要文件整理工具": 6,
            "需要测试工具": 4,
            "需要数据备份工具": 2,
            "有没有代码生成工具": 1
        }
        ranking = tool._generate_priority_ranking(gaps)
        assert len(ranking) == 4
        assert ranking[0]['priority'] == 'P0'
        assert ranking[1]['priority'] == 'P1'
        assert ranking[2]['priority'] == 'P2'
        assert ranking[3]['priority'] == 'P2'
        assert ranking[0]['occurrence_count'] == 6

    def test_run_review_default_params(self, test_log_data):
        """测试场景14：使用默认参数执行复盘成功"""
        report = task_execution_review(log_data_path=test_log_data)
        assert report['status'] == 'success'
        assert 'tool_usage_stats' in report
        assert 'time_cost_distribution' in report
        assert 'top_gap_scenarios' in report

    def test_run_review_custom_time_range(self, test_log_data):
        """测试场景15：自定义时间范围执行复盘"""
        report = task_execution_review(
            start_time="2026-02-20 00:00:00",
            end_time="2026-02-28 23:59:59",
            log_data_path=test_log_data
        )
        assert report['status'] == 'success'
        assert report['summary']['total_records'] == 11

    def test_run_review_custom_task_type(self, test_log_data):
        """测试场景16：自定义任务类型执行复盘"""
        report = task_execution_review(
            task_type="Tool Call",
            log_data_path=test_log_data
        )
        assert report['status'] == 'success'
        assert report['summary']['task_type_filter'] == 'Tool Call'

    def test_run_review_no_matching_records(self, test_log_data):
        """测试场景17：无匹配记录时返回正确提示"""
        report = task_execution_review(
            start_time="2025-01-01 00:00:00",
            end_time="2025-12-31 23:59:59",
            log_data_path=test_log_data
        )
        assert report['status'] == 'success'
        assert report['message'] == '没有匹配的记录'

    def test_run_review_invalid_time_format(self, test_log_data):
        """测试场景18：时间格式错误时返回失败"""
        report = task_execution_review(
            start_time="2026/02/01",  # 错误格式
            log_data_path=test_log_data
        )
        assert report['status'] == 'failed'
        assert '复盘分析失败' in report['message']

if __name__ == "__main__":
    pytest.main(["-v", __file__])