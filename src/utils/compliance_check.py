#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成内容合规校验核心模块，嵌入AI生成全链路执行逻辑，自动匹配对应规则操作
"""
from typing import Tuple, Dict
from pathlib import Path
import os
from datetime import datetime

# 1. 定义规则常量：存储路径映射表
STORAGE_PATH_RULES = {
    "code_skill": ["./skills/"],
    "code_tool": ["./src/tools/"],  # 工具代码
    "code_core": ["./core/", "./src/core/", "./src/agents/", "./src/business/", "./src/storage/", "./src/utils/"],
    "code_script": ["./scripts/"],
    "code_test": ["./tests/"],
    "data_system": ["./data/"],
    "data_training": ["./training/"],
    "output_report": ["./reports/"],
    "output_temp": ["./tmp/"],
    "doc": ["./docs/"],
    "design": ["./brain/docs/", "./docs/design/"]  # 设计文档
}

# 2. 定义规则常量：禁止删除的资源路径前缀
FORBID_DELETE_PATH_PREFIXES = ["./core/", "./config/", "./data/*.db", "./skills/", "./src/", "./README.md", "./requirements.txt", "./pytest.ini"]

# 3. 定义规则常量：合法临时资源路径/类型
LEGAL_TEMP_RESOURCE_FLAGS = ["./tmp/", ".tmp", ".cache", ".pyc", "__pycache__", ".pytest_cache"]

def generation_content_compliance_check(file_path: str, content_type: str, is_temporary_resource: bool = False, scene_type: str = "production") -> Tuple[bool, Dict]:
    """
    生成内容合规性校验核心函数，执行存储路径校验和临时资源标记校验
    参数:
        file_path: 待生成/存储的文件完整路径
        content_type: 内容类型，可选值：code_skill(通用可复用技能)/code_core(核心系统代码)/code_script(业务脚本)/code_test(测试用例)/data_system(系统运行数据)/data_training(训练相关数据)/output_report(分析报告)/output_temp(临时中间产物)/doc(文档类)
        is_temporary_resource: 是否标记为可删除临时资源
        scene_type: 当前运行场景，可选值：production(生产运行)/dev_test(开发测试)/iteration(系统迭代)/emergency(紧急故障排查)
    返回:
        (校验是否通过, 校验结果详情字典)
    """
    result = {
        "path_compliance": False,
        "temp_tag_compliance": False,
        "violation_details": [],
        "suggestion": ""
    }
    
    # 第一步：存储路径合规校验
    if content_type not in STORAGE_PATH_RULES:
        result["violation_details"].append(f"未知内容类型: {content_type}")
        result["suggestion"] = "请选择合法的内容类型"
        return False, result
    
    legal_path_prefixes = STORAGE_PATH_RULES[content_type]
    path_compliant = any(Path(file_path).is_relative_to(Path(prefix)) for prefix in legal_path_prefixes)
    temp_tag_compliant = True  # 初始化临时资源标记校验结果
    
    # 紧急故障排查场景特殊处理：完全豁免路径校验和临时资源标记校验
    if scene_type == "emergency":
        result["violation_details"].append("紧急排查场景临时突破存储路径规则，故障解决后24小时内需归档或清理")
        path_compliant = True
        temp_tag_compliant = True
    else:
        # 先校验：禁止在根目录直接生成文件，无论路径是否符合前缀规则
        if Path(file_path).parent == Path("."):
            result["violation_details"].append("禁止在项目根目录直接生成文件，请存入对应分类子目录")
            path_compliant = False
        # 再校验路径是否符合对应类型前缀要求
        if not path_compliant:
            result["violation_details"].append(f"存储路径不符合规则，{content_type}类型内容应存储在以下路径前缀下: {','.join(legal_path_prefixes)}")
    
    result["path_compliance"] = path_compliant
    
    # 第二步：临时资源标记合规校验（仅非紧急场景执行）
    if scene_type != "emergency":
        if is_temporary_resource:
            # 校验标记为临时的资源是否符合临时资源特征
            is_legal_temp = any(prefix in str(file_path) for prefix in LEGAL_TEMP_RESOURCE_FLAGS)
            if not is_legal_temp:
                temp_tag_compliant = False
                result["violation_details"].append("标记为可删除的临时资源不符合可删除资源判定标准，禁止标记非临时资源为可删除")
        else:
            # 校验非临时标记的资源是否属于禁止删除范畴
            is_forbid_delete = any(Path(file_path).is_relative_to(Path(prefix)) for prefix in FORBID_DELETE_PATH_PREFIXES if '*' not in prefix)
            is_forbid_delete |= any(file_path.endswith(suffix[1:]) for suffix in FORBID_DELETE_PATH_PREFIXES if '*' in suffix)
            if is_forbid_delete:
                # 禁止删除的资源不允许标记为可删除，此处已经标记为非临时，符合规则
                pass
    
    result["temp_tag_compliance"] = temp_tag_compliant
    
    # 汇总校验结果
    all_compliant = path_compliant and temp_tag_compliant
    if all_compliant and not result["violation_details"]:
        result["suggestion"] = "合规校验通过"
    elif all_compliant:
        result["suggestion"] = "合规校验通过，请注意告警提示内容"
    else:
        result["suggestion"] = "合规校验不通过，请根据违规详情修正后再执行操作"
    
    return all_compliant, result
