#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0优先级业务工具单元测试用例
"""
import os
import json
import datetime
import tempfile
import shutil
import pytest
from skills.business_skills import (
    auto_review_task_execution_records,
    auto_archive_project_files
)


class TestTaskExecutionReviewTool:
    """任务执行记录自动复盘工具测试类"""
    
    def setup_method(self):
        """测试前准备：创建临时日志目录和测试日志文件"""
        self.temp_log_dir = tempfile.mkdtemp()
        # 创建测试日志文件1
        log1_data = {
            "task_id": "task_001",
            "create_time": "2025-12-01 10:00:00",
            "tool_calls": [
                {"tool_name": "get_weather", "status": "success", "error_msg": ""},
                {"tool_name": "web_search", "status": "success", "error_msg": ""},
                {"tool_name": "non_exist_tool", "status": "failed", "error_msg": "未找到工具non_exist_tool"}
            ]
        }
        with open(os.path.join(self.temp_log_dir, "log1.json"), "w", encoding="utf-8") as f:
            json.dump(log1_data, f)
        
        # 创建测试日志文件2
        log2_data = {
            "task_id": "task_002",
            "create_time": "2025-12-01 11:00:00",
            "tool_calls": [
                {"tool_name": "get_weather", "status": "success", "error_msg": ""},
                {"tool_name": "non_exist_tool", "status": "failed", "error_msg": "未找到工具non_exist_tool"},
                {"tool_name": "non_exist_tool2", "status": "failed", "error_msg": "缺少工具non_exist_tool2"}
            ]
        }
        with open(os.path.join(self.temp_log_dir, "log2.json"), "w", encoding="utf-8") as f:
            json.dump(log2_data, f)
        
        # 创建超出时间范围的日志
        log3_data = {
            "task_id": "task_003",
            "create_time": "2025-11-30 23:00:00",
            "tool_calls": [{"tool_name": "test", "status": "success", "error_msg": ""}]
        }
        with open(os.path.join(self.temp_log_dir, "log3.json"), "w", encoding="utf-8") as f:
            json.dump(log3_data, f)
    
    def teardown_method(self):
        """测试后清理：删除临时目录"""
        shutil.rmtree(self.temp_log_dir)
    
    def test_normal_statistics(self):
        """测试正常统计功能"""
        result = auto_review_task_execution_records(
            start_time="2025-12-01 00:00:00",
            end_time="2025-12-01 23:59:59",
            log_dir=self.temp_log_dir
        )
        
        assert result["total_task_count"] == 2
        assert result["total_tool_calls"] == 6
        assert result["tool_call_success_rate"] == 50.0  # 3次成功，3次失败
        assert result["success_tool_stats"]["get_weather"] == 2
        assert result["failed_tool_stats"]["non_exist_tool"] == 2
        assert len(result["top_high_frequency_gaps"]) == 2
        assert result["top_high_frequency_gaps"][0]["occur_count"] == 2
        # 判断建议中包含对应子串即可
        assert any("建议优先开发TOP2高频缺失工具" in s for s in result["suggestions"])
    
    def test_time_format_error(self):
        """测试时间格式错误场景"""
        with pytest.raises(ValueError, match="时间格式错误"):
            auto_review_task_execution_records(
                start_time="2025/12/01",
                end_time="2025/12/02",
                log_dir=self.temp_log_dir
            )
    
    def test_start_time_after_end_time(self):
        """测试开始时间晚于结束时间场景"""
        with pytest.raises(ValueError, match="开始时间不能晚于结束时间"):
            auto_review_task_execution_records(
                start_time="2025-12-02 00:00:00",
                end_time="2025-12-01 00:00:00",
                log_dir=self.temp_log_dir
            )
    
    def test_non_exist_log_dir(self):
        """测试日志目录不存在场景"""
        with pytest.raises(FileNotFoundError, match="日志目录不存在"):
            auto_review_task_execution_records(
                start_time="2025-12-01 00:00:00",
                end_time="2025-12-01 23:59:59",
                log_dir="/non/exist/path"
            )


class TestFileArchiveTool:
    """项目文件自动分类归档工具测试类"""
    
    def setup_method(self):
        """测试前准备：创建临时源目录和测试文件"""
        self.temp_source_dir = tempfile.mkdtemp()
        self.temp_archive_dir = tempfile.mkdtemp()
        
        # 创建项目A的文件
        project_a_dir = os.path.join(self.temp_source_dir, "project_a")
        os.makedirs(project_a_dir)
        # 代码文件
        with open(os.path.join(project_a_dir, "test.py"), "w", encoding="utf-8") as f:
            f.write("print('test')")
        # 文档文件
        with open(os.path.join(project_a_dir, "readme.md"), "w", encoding="utf-8") as f:
            f.write("# Project A")
        # 图片文件
        with open(os.path.join(project_a_dir, "logo.png"), "wb") as f:
            f.write(b"fake png content")
        
        # 创建项目B的文件
        project_b_dir = os.path.join(self.temp_source_dir, "project_b")
        os.makedirs(project_b_dir)
        # 代码文件
        with open(os.path.join(project_b_dir, "index.js"), "w", encoding="utf-8") as f:
            f.write("console.log('test')")
        # 重复文件（和project_a的test.py内容相同）
        with open(os.path.join(project_b_dir, "test.py"), "w", encoding="utf-8") as f:
            f.write("print('test')")
        # 配置文件
        with open(os.path.join(project_b_dir, "config.yaml"), "w", encoding="utf-8") as f:
            f.write("key: value")
    
    def teardown_method(self):
        """测试后清理：删除临时目录"""
        shutil.rmtree(self.temp_source_dir)
        shutil.rmtree(self.temp_archive_dir)
    
    def test_normal_archive_with_duplicate_detection(self):
        """测试启用重复检测的正常归档功能"""
        result = auto_archive_project_files(
            source_dir=self.temp_source_dir,
            target_archive_root=self.temp_archive_dir,
            enable_duplicate_detection=True,
            auto_backup_original=True
        )
        
        assert result["total_processed_files"] == 6
        assert result["total_archived_files"] == 5
        assert result["duplicate_files_count"] == 1
        assert len(result["backup_path"]) > 0
        assert result["category_stats"]["code"] == 2
        assert result["category_stats"]["document"] == 1
        assert result["category_stats"]["image"] == 1
        assert result["category_stats"]["config"] == 1
        assert len(result["duplicate_files"]) == 1
        assert "test.py" in result["duplicate_files"][0]["file_path"]
        
        # 验证归档目录结构
        assert os.path.exists(os.path.join(self.temp_archive_dir, "project_a", "code", "test.py"))
        assert os.path.exists(os.path.join(self.temp_archive_dir, "project_a", "document", "readme.md"))
        assert os.path.exists(os.path.join(self.temp_archive_dir, "project_b", "code", "index.js"))
    
    def test_archive_without_duplicate_detection(self):
        """测试不启用重复检测的归档功能"""
        result = auto_archive_project_files(
            source_dir=self.temp_source_dir,
            target_archive_root=self.temp_archive_dir,
            enable_duplicate_detection=False,
            auto_backup_original=False
        )
        
        assert result["total_processed_files"] == 6
        assert result["total_archived_files"] == 6
        assert result["duplicate_files_count"] == 0
        assert result["backup_path"] == ""
    
    def test_non_exist_source_dir(self):
        """测试源目录不存在场景"""
        with pytest.raises(FileNotFoundError, match="源目录不存在"):
            auto_archive_project_files(
                source_dir="/non/exist/path",
                target_archive_root=self.temp_archive_dir
            )


if __name__ == "__main__":
    pytest.main(["-v", __file__])