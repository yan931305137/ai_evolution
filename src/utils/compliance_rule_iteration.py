#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规校验规则迭代管理模块
功能：实现规则的新增、更新、审核、生效全流程，确保新增场景下规则更新响应时长不超过24小时
"""
from typing import List, Dict, Tuple
from pathlib import Path
import json
import time
from datetime import datetime
from src.utils.compliance_check import STORAGE_PATH_RULES, FORBID_DELETE_PATH_PREFIXES, LEGAL_TEMP_RESOURCE_FLAGS

RULES_CONFIG_PATH = Path(__file__).parent.parent / "config" / "compliance_rules.json"
RULE_UPDATE_LOG_PATH = Path(__file__).parent.parent / "data" / "rule_update_logs"

class ComplianceRuleManager:
    def __init__(self):
        self.rules_config = self._load_rules_config()
        RULE_UPDATE_LOG_PATH.mkdir(exist_ok=True, parents=True)
    
    def _load_rules_config(self) -> Dict:
        """加载现有规则配置"""
        if RULES_CONFIG_PATH.exists():
            with open(RULES_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # 初始化默认规则
            default_config = {
                "STORAGE_PATH_RULES": STORAGE_PATH_RULES,
                "FORBID_DELETE_PATH_PREFIXES": FORBID_DELETE_PATH_PREFIXES,
                "LEGAL_TEMP_RESOURCE_FLAGS": LEGAL_TEMP_RESOURCE_FLAGS,
                "last_update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0.0"
            }
            self._save_rules_config(default_config)
            return default_config
    
    def _save_rules_config(self, config: Dict) -> None:
        """保存规则配置到文件"""
        with open(RULES_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def _record_rule_update(self, update_type: str, change_content: Dict, operator: str = "system_auto") -> None:
        """记录规则更新日志"""
        log_file = RULE_UPDATE_LOG_PATH / f"rule_update_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        log = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "update_type": update_type,
            "change_content": change_content,
            "operator": operator,
            "old_version": self.rules_config["version"],
            "new_version": f"{self.rules_config['version'].rsplit('.',1)[0]}.{int(self.rules_config['version'].rsplit('.',1)[1])+1}"
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    
    def propose_rule_change(self, change_type: str, rule_key: str, new_value: any, reason: str) -> Tuple[bool, Dict]:
        """
        提交规则变更提案
        参数:
            change_type: 变更类型：add/modify/delete
            rule_key: 规则所属分类：STORAGE_PATH_RULES/FORBID_DELETE_PATH_PREFIXES/LEGAL_TEMP_RESOURCE_FLAGS
            new_value: 变更内容
            reason: 变更原因，关联新增场景说明
        返回:
            (提案是否提交成功, 详情字典)
        """
        # 校验参数合法性
        if rule_key not in ["STORAGE_PATH_RULES", "FORBID_DELETE_PATH_PREFIXES", "LEGAL_TEMP_RESOURCE_FLAGS"]:
            return False, {"error": f"无效的规则分类: {rule_key}"}
        
        if change_type not in ["add", "modify", "delete"]:
            return False, {"error": f"无效的变更类型: {change_type}"}
        
        # 自动审核：简单规则变更自动审核通过，确保24小时内响应
        # 复杂规则变更可配置人工审核，此处默认自动审核通过
        audit_result = self._auto_audit_rule_change(change_type, rule_key, new_value)
        
        if audit_result["passed"]:
            # 执行规则更新
            self._execute_rule_change(change_type, rule_key, new_value)
            self._record_rule_update(change_type, {"rule_key": rule_key, "new_value": new_value, "reason": reason})
            return True, {"status": "success", "new_version": self.rules_config["version"], "audit_detail": audit_result}
        else:
            return False, {"status": "failed", "audit_detail": audit_result}
    
    def _auto_audit_rule_change(self, change_type: str, rule_key: str, new_value: any) -> Dict:
        """自动审核规则变更，确保不会破坏现有合规校验逻辑"""
        # 禁止删除核心保护路径
        if rule_key == "FORBID_DELETE_PATH_PREFIXES" and change_type == "delete":
            core_protected_paths = ["./core/", "./config/", "./skills/"]
            if any(path in new_value for path in core_protected_paths):
                return {"passed": False, "reason": "禁止删除核心系统保护路径规则"}
        
        # 禁止修改核心代码存储路径
        if rule_key == "STORAGE_PATH_RULES" and change_type == "modify":
            if "code_core" in new_value and new_value["code_core"] != ["./core/"]:
                return {"passed": False, "reason": "禁止修改核心代码存储路径规则"}
        
        return {"passed": True, "reason": "自动审核通过"}
    
    def _execute_rule_change(self, change_type: str, rule_key: str, new_value: any) -> None:
        """执行规则变更"""
        if change_type == "add":
            if isinstance(self.rules_config[rule_key], dict):
                self.rules_config[rule_key].update(new_value)
            elif isinstance(self.rules_config[rule_key], list):
                self.rules_config[rule_key].extend(new_value)
        elif change_type == "modify":
            self.rules_config[rule_key] = new_value
        elif change_type == "delete":
            if isinstance(self.rules_config[rule_key], dict):
                for k in new_value:
                    if k in self.rules_config[rule_key]:
                        del self.rules_config[rule_key][k]
            elif isinstance(self.rules_config[rule_key], list):
                for v in new_value:
                    if v in self.rules_config[rule_key]:
                        self.rules_config[rule_key].remove(v)
        
        # 更新版本号和更新时间
        self.rules_config["version"] = f"{self.rules_config['version'].rsplit('.',1)[0]}.{int(self.rules_config['version'].rsplit('.',1)[1])+1}"
        self.rules_config["last_update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存更新后的配置
        self._save_rules_config(self.rules_config)
    
    def get_current_rules(self) -> Dict:
        """获取当前生效的所有规则"""
        return self.rules_config

# 全局规则管理器实例
rule_manager = ComplianceRuleManager()
