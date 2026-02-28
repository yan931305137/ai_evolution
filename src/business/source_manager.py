#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心业务逻辑模块
协调配置、Web Tools、评估器等工具，实现完整的业务流程：
1. 低质源识别规则引擎
2. 优质源多维度筛选评分模型
3. 有效信息占比自动统计
4. 低质源自动取消订阅/清理执行
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from src.utils.channel_config import channel_config
from src.utils.source_evaluator import source_evaluator

logger = logging.getLogger(__name__)


class SourceQuality(Enum):
    """信息源质量等级"""
    HIGH = "high"      # 优质
    MEDIUM = "medium"  # 中等
    LOW = "low"       # 低质


class SourceStatus(Enum):
    """信息源状态"""
    ACTIVE = "active"           # 活跃
    INACTIVE = "inactive"       # 非活跃
    MARKED_FOR_CLEANUP = "marked_for_cleanup"  # 标记清理
    CLEANED = "cleaned"         # 已清理


@dataclass
class SourceInfo:
    """信息源信息数据类"""
    url: str
    title: str = ""
    category: str = ""
    
    # 质量指标
    authority_score: float = 0.0
    stability_score: float = 0.0
    content_score: float = 0.0
    overall_score: float = 0.0
    ad_ratio: float = 0.0
    
    # 状态信息
    quality_level: SourceQuality = SourceQuality.MEDIUM
    status: SourceStatus = SourceStatus.ACTIVE
    
    # 统计信息
    days_since_last_update: int = 0
    error_rate: float = 0.0
    update_count: int = 0
    last_evaluation_time: str = ""
    
    # 清理信息
    cleanup_reason: str = ""
    cleanup_time: str = ""
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class SourceManager:
    """信息源管理器 - 核心业务逻辑"""
    
    def __init__(self):
        """初始化信息源管理器"""
        self.config = channel_config
        self.evaluator = source_evaluator
        self.sources: Dict[str, SourceInfo] = {}
        self.cleanup_history: List[Dict[str, Any]] = []
        
        logger.info("信息源管理器初始化完成")
    
    # ============================================
    # 1. 低质源识别规则引擎
    # ============================================
    
    def identify_low_quality_sources(self) -> List[SourceInfo]:
        """
        识别低质信息源
        
        Returns:
            低质信息源列表
        """
        logger.info("开始识别低质信息源")
        
        low_quality_sources = []
        
        for url, source in self.sources.items():
            if source.status == SourceStatus.CLEANED:
                continue
            
            # 检查是否为低质源
            is_low_quality, reason = self._check_if_low_quality(source)
            
            if is_low_quality:
                source.status = SourceStatus.MARKED_FOR_CLEANUP
                source.cleanup_reason = reason
                low_quality_sources.append(source)
                logger.warning(f"识别到低质源: {url} - {reason}")
        
        logger.info(f"识别到 {len(low_quality_sources)} 个低质信息源")
        
        return low_quality_sources
    
    def _check_if_low_quality(self, source: SourceInfo) -> tuple[bool, str]:
        """
        检查信息源是否为低质源
        
        Args:
            source: 信息源信息
            
        Returns:
            (是否低质, 原因说明)
        """
        # 使用配置中的清理规则
        should_cleanup, reason = self.config.should_cleanup_source({
            'days_since_last_update': source.days_since_last_update,
            'ad_ratio': source.ad_ratio,
            'quality_score': source.content_score,
            'error_rate': source.error_rate
        })
        
        return should_cleanup, reason
    
    # ============================================
    # 2. 优质源多维度筛选评分模型
    # ============================================
    
    def filter_high_quality_sources(self, sources: Optional[List[SourceInfo]] = None) -> List[SourceInfo]:
        """
        筛选优质信息源
        
        Args:
            sources: 信息源列表，如果为None则使用管理器中的所有源
            
        Returns:
            优质信息源列表
        """
        logger.info("开始筛选优质信息源")
        
        if sources is None:
            sources = list(self.sources.values())
        
        high_quality_sources = []
        
        thresholds = self.config.get_screening_thresholds()
        
        for source in sources:
            if source.status == SourceStatus.CLEANED:
                continue
            
            # 检查是否满足优质源标准
            is_high_quality = self.config.is_high_quality_source({
                'authority': source.authority_score,
                'stability': source.stability_score,
                'content': source.content_score,
                'overall': source.overall_score
            })
            
            if is_high_quality:
                source.quality_level = SourceQuality.HIGH
                high_quality_sources.append(source)
                logger.info(f"优质源: {source.url} - 综合评分: {source.overall_score}")
        
        logger.info(f"筛选出 {len(high_quality_sources)} 个优质信息源")
        
        return high_quality_sources
    
    def rank_sources_by_quality(self, sources: Optional[List[SourceInfo]] = None) -> List[SourceInfo]:
        """
        按质量对信息源进行排序
        
        Args:
            sources: 信息源列表，如果为None则使用管理器中的所有源
            
        Returns:
            按质量排序的信息源列表（从高到低）
        """
        if sources is None:
            sources = list(self.sources.values())
        
        # 过滤掉已清理的源
        active_sources = [s for s in sources if s.status != SourceStatus.CLEANED]
        
        # 按综合评分排序（从高到低）
        ranked = sorted(active_sources, key=lambda x: x.overall_score, reverse=True)
        
        # 更新质量等级
        for source in ranked:
            if source.overall_score >= 80:
                source.quality_level = SourceQuality.HIGH
            elif source.overall_score >= 60:
                source.quality_level = SourceQuality.MEDIUM
            else:
                source.quality_level = SourceQuality.LOW
        
        return ranked
    
    # ============================================
    # 3. 有效信息占比自动统计
    # ============================================
    
    def calculate_effectiveness_metrics(self) -> Dict[str, Any]:
        """
        计算有效性指标
        
        Returns:
            有效性指标字典
        """
        logger.info("开始计算有效性指标")
        
        sources = list(self.sources.values())
        active_sources = [s for s in sources if s.status != SourceStatus.CLEANED]
        
        if not active_sources:
            return {
                'total_count': 0,
                'active_count': 0,
                'message': '没有活跃的信息源'
            }
        
        total = len(active_sources)
        high_quality = sum(1 for s in active_sources if s.quality_level == SourceQuality.HIGH)
        medium_quality = sum(1 for s in active_sources if s.quality_level == SourceQuality.MEDIUM)
        low_quality = sum(1 for s in active_sources if s.quality_level == SourceQuality.LOW)
        
        # 计算平均指标
        avg_overall = sum(s.overall_score for s in active_sources) / total
        avg_ad_ratio = sum(s.ad_ratio for s in active_sources) / total
        avg_error_rate = sum(s.error_rate for s in active_sources) / total
        
        # 计算有效信息占比
        effective_ratio = high_quality / total if total > 0 else 0
        
        metrics = {
            'total_count': total,
            'active_count': total,
            'quality_distribution': {
                'high_quality_count': high_quality,
                'high_quality_rate': round(high_quality / total * 100, 2),
                'medium_quality_count': medium_quality,
                'medium_quality_rate': round(medium_quality / total * 100, 2),
                'low_quality_count': low_quality,
                'low_quality_rate': round(low_quality / total * 100, 2)
            },
            'averages': {
                'overall_score': round(avg_overall, 2),
                'ad_ratio': round(avg_ad_ratio, 3),
                'error_rate': round(avg_error_rate, 3)
            },
            'effectiveness': {
                'effective_info_ratio': round(effective_ratio, 2),  # 有效信息占比
                'low_quality_ratio': round(low_quality / total, 2) if total > 0 else 0  # 低质源占比
            },
            'update_status': {
                'recently_updated': sum(1 for s in active_sources if s.days_since_last_update <= 30),
                'stale': sum(1 for s in active_sources if s.days_since_last_update > 90)
            }
        }
        
        logger.info(f"有效性指标计算完成: 优质率 {metrics['effectiveness']['effective_info_ratio']*100:.1f}%")
        
        return metrics
    
    # ============================================
    # 4. 低质源自动清理执行
    # ============================================
    
    def auto_cleanup_low_quality_sources(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        自动清理低质信息源
        
        Args:
            dry_run: 是否为试运行模式（不真正清理）
            
        Returns:
            清理结果字典
        """
        logger.info(f"开始自动清理低质信息源 (试运行模式: {dry_run})")
        
        # 识别低质源
        low_quality_sources = self.identify_low_quality_sources()
        
        if not low_quality_sources:
            return {
                'total': 0,
                'cleaned': 0,
                'skipped': 0,
                'message': '没有需要清理的低质信息源'
            }
        
        # 获取自动清理配置
        cleanup_config = self.config.get_auto_cleanup_config()
        
        # 检查是否启用自动清理
        if not cleanup_config.get('enabled', True) and not dry_run:
            return {
                'total': len(low_quality_sources),
                'cleaned': 0,
                'skipped': len(low_quality_sources),
                'message': '自动清理未启用'
            }
        
        # 限制批量大小
        batch_size = cleanup_config.get('batch_size', 100)
        sources_to_cleanup = low_quality_sources[:batch_size]
        
        cleaned_count = 0
        skipped_count = 0
        
        for source in sources_to_cleanup:
            try:
                if dry_run:
                    # 试运行模式：只记录，不真正清理
                    logger.info(f"[试运行] 将清理: {source.url} - {source.cleanup_reason}")
                    cleaned_count += 1
                else:
                    # 真正清理
                    if self._cleanup_source(source):
                        cleaned_count += 1
                        # 记录清理历史
                        self.cleanup_history.append({
                            'url': source.url,
                            'reason': source.cleanup_reason,
                            'time': datetime.now().isoformat(),
                            'quality_score': source.overall_score,
                            'ad_ratio': source.ad_ratio
                        })
                    else:
                        skipped_count += 1
            except Exception as e:
                logger.error(f"清理失败 {source.url}: {str(e)}")
                skipped_count += 1
        
        result = {
            'total': len(sources_to_cleanup),
            'cleaned': cleaned_count,
            'skipped': skipped_count,
            'dry_run': dry_run,
            'message': f"{'试运行: ' if dry_run else ''}清理完成"
        }
        
        logger.info(f"自动清理完成: 总计 {result['total']}, 成功 {result['cleaned']}, 跳过 {result['skipped']}")
        
        return result
    
    def _cleanup_source(self, source: SourceInfo) -> bool:
        """
        清理单个信息源
        
        Args:
            source: 信息源信息
            
        Returns:
            是否清理成功
        """
        try:
            # 获取清理配置
            cleanup_rules = self.config.get_cleanup_rules()
            cleanup_execution = cleanup_rules.get('cleanup_execution', {})
            
            # 根据配置执行清理
            if cleanup_execution.get('mark_as_disabled', True):
                # 标记为不可用（不删除）
                source.status = SourceStatus.CLEANED
                source.cleanup_time = datetime.now().isoformat()
                logger.info(f"已清理（标记为不可用）: {source.url}")
                return True
            
            elif cleanup_execution.get('unsubscribe_enabled', False):
                # 取消订阅（模拟操作）
                source.status = SourceStatus.CLEANED
                source.cleanup_time = datetime.now().isoformat()
                logger.info(f"已取消订阅: {source.url}")
                return True
            
            elif cleanup_execution.get('permanent_delete', False):
                # 完全删除
                if source.url in self.sources:
                    del self.sources[source.url]
                logger.info(f"已完全删除: {source.url}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"清理信息源失败: {str(e)}")
            return False
    
    # ============================================
    # 信息源管理功能
    # ============================================
    
    def add_source(self, url: str, evaluate: bool = True) -> SourceInfo:
        """
        添加信息源
        
        Args:
            url: 信息源URL
            evaluate: 是否立即评估
            
        Returns:
            信息源信息对象
        """
        logger.info(f"添加信息源: {url}")
        
        # 如果已存在，返回现有的
        if url in self.sources:
            logger.info(f"信息源已存在: {url}")
            return self.sources[url]
        
        # 创建新的信息源对象
        source = SourceInfo(url=url)
        
        # 如果需要评估
        if evaluate:
            evaluation_result = self.evaluator.evaluate_single_source(url)
            
            if evaluation_result['success']:
                # 更新信息源信息
                source.title = evaluation_result.get('content_info', {}).get('title', '')
                source.category = evaluation_result.get('classification', {}).get('category', '')
                
                # 更新质量指标
                source.authority_score = evaluation_result.get('quality_metrics', {}).get('authority_score', 0)
                source.stability_score = evaluation_result.get('quality_metrics', {}).get('stability_score', 0)
                source.content_score = evaluation_result.get('quality_metrics', {}).get('content_score', 0)
                source.overall_score = evaluation_result.get('quality_metrics', {}).get('overall_score', 0)
                source.ad_ratio = evaluation_result.get('ad_metrics', {}).get('ad_ratio', 0)
                
                # 更新状态
                source.last_evaluation_time = datetime.now().isoformat()
                
                logger.info(f"信息源评估完成: {url}, 综合评分: {source.overall_score}")
            else:
                logger.warning(f"信息源评估失败: {url}, 错误: {evaluation_result.get('error', 'Unknown')}")
        
        # 添加到管理器
        self.sources[url] = source
        
        return source
    
    def add_multiple_sources(self, urls: List[str], evaluate: bool = True) -> List[SourceInfo]:
        """
        批量添加信息源
        
        Args:
            urls: URL列表
            evaluate: 是否立即评估
            
        Returns:
            信息源信息列表
        """
        logger.info(f"批量添加 {len(urls)} 个信息源")
        
        sources = []
        for url in urls:
            try:
                source = self.add_source(url, evaluate=evaluate)
                sources.append(source)
            except Exception as e:
                logger.error(f"添加信息源失败 {url}: {str(e)}")
        
        return sources
    
    def get_source(self, url: str) -> Optional[SourceInfo]:
        """
        获取信息源信息
        
        Args:
            url: 信息源URL
            
        Returns:
            信息源信息对象，如果不存在则返回None
        """
        return self.sources.get(url)
    
    def get_all_sources(self, status: Optional[SourceStatus] = None) -> List[SourceInfo]:
        """
        获取所有信息源
        
        Args:
            status: 状态过滤，如果为None则返回所有
            
        Returns:
            信息源列表
        """
        sources = list(self.sources.values())
        
        if status:
            sources = [s for s in sources if s.status == status]
        
        return sources
    
    def update_source_stats(self, url: str, stats: Dict[str, Any]) -> bool:
        """
        更新信息源统计信息
        
        Args:
            url: 信息源URL
            stats: 统计信息字典
            
        Returns:
            是否更新成功
        """
        if url not in self.sources:
            logger.warning(f"信息源不存在: {url}")
            return False
        
        source = self.sources[url]
        
        # 更新统计信息
        if 'days_since_last_update' in stats:
            source.days_since_last_update = stats['days_since_last_update']
        if 'error_rate' in stats:
            source.error_rate = stats['error_rate']
        if 'update_count' in stats:
            source.update_count = stats['update_count']
        
        logger.info(f"更新信息源统计信息: {url}")
        
        return True
    
    def generate_cleanup_report(self) -> Dict[str, Any]:
        """
        生成清理报告
        
        Returns:
            清理报告字典
        """
        report = {
            'generated_time': datetime.now().isoformat(),
            'total_sources': len(self.sources),
            'cleanup_history_count': len(self.cleanup_history),
            'cleanup_history': self.cleanup_history[-10:]  # 最近10条记录
        }
        
        # 统计各状态数量
        status_count = {}
        for source in self.sources.values():
            status = source.status.value
            status_count[status] = status_count.get(status, 0) + 1
        
        report['status_distribution'] = status_count
        
        return report


# 全局信息源管理器实例
source_manager = SourceManager()
