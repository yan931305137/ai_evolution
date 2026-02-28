#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息获取渠道配置管理工具
提供分类、筛选、清理等业务配置的访问接口
"""

import logging
from typing import Dict, List, Any, Optional
from src.utils.config import cfg

logger = logging.getLogger(__name__)


class ChannelConfig:
    """信息渠道配置管理类"""
    
    def __init__(self):
        """初始化配置管理器"""
        cfg.load()
    
    def get_classification_categories(self) -> List[Dict[str, Any]]:
        """
        获取分类标签列表
        Returns:
            分类标签列表，每个标签包含 name, description, priority
        """
        categories = cfg.get("classification.categories", [])
        return categories
    
    def get_auto_classification_rules(self) -> List[Dict[str, Any]]:
        """
        获取自动分类规则
        Returns:
            自动分类规则列表
        """
        rules = cfg.get("classification.auto_classification_rules", [])
        return rules
    
    def classify_by_keywords(self, url: str, title: str = "") -> Optional[str]:
        """
        根据关键词自动分类信息源
        Args:
            url: 信息源URL
            title: 信息源标题（可选）
        Returns:
            分类名称，如果无法分类则返回 None
        """
        text = (url + " " + title).lower()
        rules = self.get_auto_classification_rules()
        
        for rule in rules:
            patterns = rule.get("keyword_pattern", [])
            target_category = rule.get("target_category", "")
            
            for pattern in patterns:
                if pattern.lower() in text:
                    logger.debug(f"匹配到关键词 '{pattern}'，分类为: {target_category}")
                    return target_category
        
        return None
    
    def get_screening_thresholds(self) -> Dict[str, Any]:
        """
        获取筛选阈值配置
        Returns:
            筛选阈值字典
        """
        thresholds = cfg.get("screening_criteria.quality_source_threshold", {})
        return thresholds
    
    def get_quality_scoring_weights(self) -> Dict[str, Dict[str, float]]:
        """
        获取质量评分权重配置
        Returns:
            评分权重字典，包含 authority, stability, content_quality
        """
        weights = cfg.get("screening_criteria.quality_scoring", {})
        return weights
    
    def get_ad_detection_config(self) -> Dict[str, Any]:
        """
        获取广告检测配置
        Returns:
            广告检测配置字典
        """
        config = cfg.get("screening_criteria.ad_detection", {})
        return config
    
    def calculate_overall_score(self, authority: float, stability: float, content: float) -> float:
        """
        计算综合评分
        Args:
            authority: 权威性评分（0-100）
            stability: 稳定性评分（0-100）
            content: 内容质量评分（0-100）
        Returns:
            综合评分（0-100）
        """
        # 获取阈值配置
        thresholds = self.get_screening_thresholds()
        
        # 使用加权平均计算综合分（权重各占1/3）
        overall = (authority + stability + content) / 3
        return round(overall, 2)
    
    def is_high_quality_source(self, scores: Dict[str, float]) -> bool:
        """
        判断是否为优质信息源
        Args:
            scores: 包含 authority, stability, content, overall 的评分字典
        Returns:
            是否为优质源
        """
        thresholds = self.get_screening_thresholds()
        
        return (
            scores.get("authority", 0) >= thresholds.get("min_authority_score", 60) and
            scores.get("stability", 0) >= thresholds.get("min_stability_score", 50) and
            scores.get("content", 0) >= thresholds.get("min_content_score", 55) and
            scores.get("overall", 0) >= thresholds.get("min_overall_score", 65)
        )
    
    def get_cleanup_rules(self) -> Dict[str, Any]:
        """
        获取清理规则配置
        Returns:
            清理规则字典
        """
        rules = cfg.get("cleanup_rules", {})
        return rules
    
    def should_cleanup_source(self, source_data: Dict[str, Any]) -> tuple[bool, str]:
        """
        判断是否应该清理某个信息源
        Args:
            source_data: 信息源数据字典
        Returns:
            (是否应该清理, 原因说明)
        """
        rules = self.get_cleanup_rules()
        low_quality_rules = rules.get("low_quality_identification", {})
        
        # 1. 检查是否长期未更新
        no_update_days = source_data.get("days_since_last_update", 0)
        threshold = low_quality_rules.get("no_update_threshold_days", 90)
        if no_update_days > threshold:
            return True, f"超过{threshold}天未更新（{no_update_days}天）"
        
        # 2. 检查广告占比
        ad_ratio = source_data.get("ad_ratio", 0)
        max_ad_ratio = low_quality_rules.get("max_ad_ratio", 0.4)
        if ad_ratio > max_ad_ratio:
            return True, f"广告占比过高（{ad_ratio*100:.1f}% > {max_ad_ratio*100:.1f}%）"
        
        # 3. 检查质量评分
        quality_score = source_data.get("quality_score", 100)
        min_score = low_quality_rules.get("min_quality_score", 30)
        if quality_score < min_score:
            return True, f"质量评分过低（{quality_score} < {min_score}）"
        
        # 4. 检查错误率
        error_rate = source_data.get("error_rate", 0)
        max_error_rate = low_quality_rules.get("max_error_rate", 0.5)
        if error_rate > max_error_rate:
            return True, f"错误率过高（{error_rate*100:.1f}% > {max_error_rate*100:.1f}%）"
        
        return False, "符合保留标准"
    
    def get_auto_cleanup_config(self) -> Dict[str, Any]:
        """
        获取自动清理配置
        Returns:
            自动清理配置字典
        """
        config = cfg.get("cleanup_rules.auto_cleanup", {})
        return config
    
    def get_analytics_config(self) -> Dict[str, Any]:
        """
        获取统计分析配置
        Returns:
            统计分析配置字典
        """
        config = cfg.get("analytics", {})
        return config
    
    def get_effectiveness_metrics(self) -> List[str]:
        """
        获取有效性指标列表
        Returns:
            指标名称列表
        """
        config = self.get_analytics_config()
        metrics = config.get("effectiveness_metrics.metrics", [])
        return metrics
    
    def validate_config(self) -> tuple[bool, List[str]]:
        """
        验证配置完整性
        Returns:
            (是否有效, 问题列表)
        """
        issues = []
        
        # 检查分类标签
        categories = self.get_classification_categories()
        if not categories:
            issues.append("未定义任何分类标签")
        
        # 检查筛选阈值
        thresholds = self.get_screening_thresholds()
        if not thresholds:
            issues.append("未配置筛选阈值")
        
        # 检查清理规则
        cleanup_rules = self.get_cleanup_rules()
        if not cleanup_rules:
            issues.append("未配置清理规则")
        
        # 检查评分权重
        weights = self.get_quality_scoring_weights()
        if not weights:
            issues.append("未配置质量评分权重")
        
        return len(issues) == 0, issues


# 全局配置实例
channel_config = ChannelConfig()
