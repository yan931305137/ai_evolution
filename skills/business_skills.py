#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务工具类技能模块 - 存储业务场景相关的工具/技能
"""
import os
import json
import datetime
import hashlib
import shutil
from collections import defaultdict, Counter
from typing import List, Dict, Tuple

def auto_review_task_execution_records(
    start_time: str,
    end_time: str,
    log_dir: str = "data/task_logs",
    top_n_gaps: int = 5
) -> Dict:
    """
    【功能说明】任务执行记录自动复盘工具
    自动拉取指定时间范围内所有任务执行日志，统计工具调用成功率、失败场景，自动识别高频工具缺口
    
    【入参规范】
    :param start_time: 统计开始时间，格式要求：YYYY-MM-DD HH:MM:SS
    :param end_time: 统计结束时间，格式要求：YYYY-MM-DD HH:MM:SS
    :param log_dir: 任务日志存储目录路径，默认值：data/task_logs
    :param top_n_gaps: 返回排名前N的高频工具缺口，默认值：5
    
    【出参规范】
    返回字典结构：
    {
        "statistical_period": {"start_time": str, "end_time": str},  # 统计周期
        "total_task_count": int,  # 总任务数
        "total_tool_calls": int,  # 总工具调用次数
        "tool_call_success_rate": float,  # 工具调用成功率(百分比，保留2位小数)
        "success_tool_stats": Dict[str, int],  # 各工具成功调用次数统计
        "failed_tool_stats": Dict[str, int],  # 各工具失败调用次数统计
        "failure_scenarios": List[Dict],  # 失败场景详情列表
        "top_high_frequency_gaps": List[Dict],  # TOP N高频工具缺口列表
        "suggestions": List[str]  # 优化建议列表
    }
    """
    # 1. 时间格式校验与转换
    try:
        start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise ValueError(f"时间格式错误，请使用YYYY-MM-DD HH:MM:SS格式：{str(e)}")
    
    if start_dt >= end_dt:
        raise ValueError("开始时间不能晚于结束时间")
    
    # 2. 日志目录校验
    if not os.path.exists(log_dir):
        raise FileNotFoundError(f"日志目录不存在：{log_dir}")
    
    # 3. 初始化统计变量
    total_task_count = 0
    total_tool_calls = 0
    success_calls = 0
    failed_calls = 0
    success_tool_stats = defaultdict(int)
    failed_tool_stats = defaultdict(int)
    failure_scenarios = []
    gap_records = []
    
    # 4. 遍历日志文件
    for root, _, files in os.walk(log_dir):
        for file in files:
            if not file.endswith('.json'):
                continue
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            except Exception:
                continue
            
            # 校验日志时间是否在统计范围内
            log_time_str = log_data.get('create_time', '')
            try:
                log_dt = datetime.datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
            except:
                continue
            
            if not (start_dt <= log_dt <= end_dt):
                continue
            
            total_task_count += 1
            
            # 提取工具调用记录
            tool_calls = log_data.get('tool_calls', [])
            for call in tool_calls:
                total_tool_calls += 1
                tool_name = call.get('tool_name', '')
                call_status = call.get('status', 'failed')
                error_msg = call.get('error_msg', '')
                
                if call_status == 'success':
                    success_calls += 1
                    success_tool_stats[tool_name] += 1
                else:
                    failed_calls += 1
                    failed_tool_stats[tool_name] += 1
                    failure_scenarios.append({
                        "task_id": log_data.get('task_id', ''),
                        "tool_name": tool_name,
                        "error_msg": error_msg,
                        "occur_time": log_time_str
                    })
                    
                    # 识别工具缺口：错误信息包含工具缺失、未找到、不支持等关键词
                    gap_keywords = ['缺少工具', '未找到工具', '工具不存在', '不支持该功能', '无对应工具', '工具缺失']
                    if any(keyword in error_msg for keyword in gap_keywords):
                        gap_records.append(error_msg)
    
    # 5. 计算成功率
    success_rate = 0.0
    if total_tool_calls > 0:
        success_rate = round((success_calls / total_tool_calls) * 100, 2)
    
    # 6. 统计高频缺口
    gap_counter = Counter(gap_records)
    top_gaps = []
    for gap_desc, count in gap_counter.most_common(top_n_gaps):
        top_gaps.append({
            "gap_description": gap_desc,
            "occur_count": count,
            "proportion": round((count / len(gap_records)) * 100, 2) if gap_records else 0.0
        })
    
    # 7. 生成优化建议
    suggestions = []
    if success_rate < 90:
        suggestions.append("工具调用成功率低于90%，建议优先优化失败率Top3的工具")
    if top_gaps:
        suggestions.append(f"建议优先开发TOP{len(top_gaps)}高频缺失工具，覆盖{round(sum([g['occur_count'] for g in top_gaps])/len(gap_records)*100, 2)}%的缺口场景")
    
    # 8. 组装返回结果
    return {
        "statistical_period": {
            "start_time": start_time,
            "end_time": end_time
        },
        "total_task_count": total_task_count,
        "total_tool_calls": total_tool_calls,
        "tool_call_success_rate": success_rate,
        "success_tool_stats": dict(success_tool_stats),
        "failed_tool_stats": dict(failed_tool_stats),
        "failure_scenarios": failure_scenarios,
        "top_high_frequency_gaps": top_gaps,
        "suggestions": suggestions
    }


def auto_archive_project_files(
    source_dir: str,
    target_archive_root: str = "data/archived_files",
    enable_duplicate_detection: bool = True,
    auto_backup_original: bool = True
) -> Dict:
    """
    【功能说明】项目文件自动分类归档工具
    自动识别文件类型、归属项目，按预设规则分类归档，重复文件检测标注，自动备份原始文件避免误删
    
    【入参规范】
    :param source_dir: 待整理的源文件目录路径
    :param target_archive_root: 归档文件存储根目录路径，默认值：data/archived_files
    :param enable_duplicate_detection: 是否启用重复文件检测，默认值：True
    :param auto_backup_original: 是否自动备份原始文件，默认值：True
    
    【出参规范】
    返回字典结构：
    {
        "source_dir": str,  # 源目录路径
        "target_archive_root": str,  # 归档根目录路径
        "total_processed_files": int,  # 总处理文件数
        "total_archived_files": int,  # 已归档文件数
        "duplicate_files_count": int,  # 重复文件数量
        "backup_path": str,  # 原始文件备份路径（如果启用备份）
        "category_stats": Dict[str, int],  # 各分类归档文件数统计
        "duplicate_files": List[Dict],  # 重复文件详情列表
        "failed_files": List[Dict]  # 处理失败文件列表
    }
    """
    # 1. 目录校验
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"源目录不存在：{source_dir}")
    
    # 创建归档根目录
    os.makedirs(target_archive_root, exist_ok=True)
    
    # 2. 配置文件分类规则
    FILE_TYPE_MAPPING = {
        'code': ['.py', '.java', '.js', '.ts', '.go', '.cpp', '.c', '.php', '.html', '.css', '.vue', '.react', '.sql'],
        'document': ['.md', '.doc', '.docx', '.pdf', '.txt', '.ppt', '.pptx', '.xls', '.xlsx', '.csv'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'video': ['.mp4', '.avi', '.mov', '.flv', '.wmv', '.mkv'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
        'config': ['.json', '.yaml', '.yml', '.ini', '.conf', '.env', '.xml'],
        'compressed': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'executable': ['.exe', '.bin', '.sh', '.bat', '.cmd', '.app']
    }
    
    # 3. 初始化变量
    total_processed = 0
    total_archived = 0
    duplicate_count = 0
    category_stats = defaultdict(int)
    duplicate_files = []
    failed_files = []
    file_hash_map = {}  # 存储文件哈希值，用于重复检测
    backup_path = ""
    
    # 4. 自动备份原始文件
    if auto_backup_original:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir_name = f"original_backup_{timestamp}"
        backup_path = os.path.join(target_archive_root, backup_dir_name)
        shutil.copytree(source_dir, backup_path)
    
    # 5. 遍历源目录所有文件
    for root, _, files in os.walk(source_dir):
        for file in files:
            total_processed += 1
            file_path = os.path.join(root, file)
            
            # 跳过符号链接避免循环
            if os.path.islink(file_path):
                continue
            
            try:
                # 识别文件类型和分类
                file_ext = os.path.splitext(file)[1].lower()
                file_category = 'other'
                for category, exts in FILE_TYPE_MAPPING.items():
                    if file_ext in exts:
                        file_category = category
                        break
                
                # 归属项目识别：取相对于源目录的第一层目录作为项目名
                relative_path = os.path.relpath(root, source_dir)
                project_name = relative_path.split(os.sep)[0] if relative_path != '.' else 'unknown_project'
                
                # 重复文件检测
                is_duplicate = False
                if enable_duplicate_detection:
                    # 计算文件MD5哈希
                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    file_hash = hash_md5.hexdigest()
                    
                    if file_hash in file_hash_map:
                        is_duplicate = True
                        duplicate_count += 1
                        duplicate_files.append({
                            "file_path": file_path,
                            "duplicate_with": file_hash_map[file_hash],
                            "file_size": os.path.getsize(file_path)
                        })
                    else:
                        file_hash_map[file_hash] = file_path
                
                if not is_duplicate:
                    # 创建归档目录结构：归档根目录/项目名/文件分类
                    archive_dir = os.path.join(target_archive_root, project_name, file_category)
                    os.makedirs(archive_dir, exist_ok=True)
                    
                    # 移动文件到归档目录，重名文件加时间戳后缀
                    target_file_path = os.path.join(archive_dir, file)
                    if os.path.exists(target_file_path):
                        name, ext = os.path.splitext(file)
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_file_path = os.path.join(archive_dir, f"{name}_{timestamp}{ext}")
                    
                    shutil.move(file_path, target_file_path)
                    total_archived += 1
                    category_stats[file_category] += 1
            
            except Exception as e:
                failed_files.append({
                    "file_path": file_path,
                    "error_msg": str(e)
                })
    
    # 6. 组装返回结果
    return {
        "source_dir": source_dir,
        "target_archive_root": target_archive_root,
        "total_processed_files": total_processed,
        "total_archived_files": total_archived,
        "duplicate_files_count": duplicate_count,
        "backup_path": backup_path,
        "category_stats": dict(category_stats),
        "duplicate_files": duplicate_files,
        "failed_files": failed_files
    }