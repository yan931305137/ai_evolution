#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信息源评估流程集成工具
集成网页爬取、广告识别、内容评分等功能，完成信息源的综合评估
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from src.tools.web_tools import analyze_webpage, batch_analyze_webpages
from src.utils.channel_config import channel_config

logger = logging.getLogger(__name__)


class SourceEvaluator:
    """信息源评估器"""
    
    def __init__(self):
        """初始化评估器"""
        self.config = channel_config
    
    def evaluate_single_source(self, url: str) -> Dict[str, Any]:
        """
        评估单个信息源
        
        Args:
            url: 信息源URL
            
        Returns:
            评估结果字典
        """
        logger.info(f"开始评估信息源: {url}")
        
        # 1. 爬取并分析网页
        page_analysis = analyze_webpage(url)
        
        if not page_analysis['success']:
            return {
                'url': url,
                'evaluation_time': datetime.now().isoformat(),
                'success': False,
                'error': page_analysis.get('error', 'Unknown error')
            }
        
        # 2. 自动分类
        category = self.config.classify_by_keywords(url, page_analysis.get('title', ''))
        
        # 3. 计算质量评分（使用已有的质量评分）
        content_score = page_analysis.get('quality_score', 0)
        
        # 4. 计算权威性评分
        authority_score = self._calculate_authority_score(url, page_analysis)
        
        # 5. 计算稳定性评分（基于更新频率，这里简化处理）
        stability_score = self._calculate_stability_score(page_analysis)
        
        # 6. 获取广告占比
        ad_ratio = page_analysis.get('ad_ratio', 0.0)
        
        # 7. 计算综合评分
        overall_score = self.config.calculate_overall_score(
            authority_score,
            stability_score,
            content_score
        )
        
        # 8. 判断是否为优质源
        is_quality = self.config.is_high_quality_source({
            'authority': authority_score,
            'stability': stability_score,
            'content': content_score,
            'overall': overall_score
        })
        
        # 9. 判断是否应该清理
        should_cleanup, cleanup_reason = self.config.should_cleanup_source({
            'days_since_last_update': 30,  # 默认值，实际应从历史数据获取
            'ad_ratio': ad_ratio,
            'quality_score': content_score,
            'error_rate': 0.1  # 默认值
        })
        
        # 10. 组装评估结果
        result = {
            'url': url,
            'evaluation_time': datetime.now().isoformat(),
            'success': True,
            'classification': {
                'category': category,
                'auto_classified': category is not None
            },
            'quality_metrics': {
                'authority_score': authority_score,
                'stability_score': stability_score,
                'content_score': content_score,
                'overall_score': overall_score,
                'is_high_quality': is_quality
            },
            'ad_metrics': {
                'ad_ratio': ad_ratio,
                'exceeds_threshold': ad_ratio > self.config.get_screening_thresholds().get('max_ad_ratio', 0.25)
            },
            'content_info': {
                'title': page_analysis.get('title', ''),
                'content_length': page_analysis.get('content_length', 0),
                'metadata': page_analysis.get('metadata', {})
            },
            'evaluation': {
                'should_cleanup': should_cleanup,
                'cleanup_reason': cleanup_reason if should_cleanup else '符合保留标准',
                'recommendation': self._get_recommendation(is_quality, should_cleanup, ad_ratio)
            }
        }
        
        logger.info(f"信息源评估完成: {url}, 综合评分: {overall_score}")
        
        return result
    
    def evaluate_multiple_sources(self, urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        批量评估多个信息源
        
        Args:
            urls: 信息源URL列表
            delay: 请求之间的延迟（秒）
            
        Returns:
            评估结果列表
        """
        logger.info(f"开始批量评估 {len(urls)} 个信息源")
        
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"评估进度: {i+1}/{len(urls)} - {url}")
            
            result = self.evaluate_single_source(url)
            results.append(result)
            
            # 添加延迟
            if i < len(urls) - 1:
                import time
                time.sleep(delay)
        
        # 生成汇总报告
        summary = self._generate_evaluation_summary(results)
        
        return results
    
    def evaluate_reliability(self, source_type: str, source_content: str = '') -> float:
        """
        评估信息源的可靠性评分

        Args:
            source_type: 信息源类型
                - knowledge_base: 知识库 (最可靠)
                - web_search: 网页搜索 (较可靠)
                - memory: 历史记忆 (中等可靠)
                - user_input: 用户输入 (低可靠，需验证)
                - model_inference: 模型推理 (低可靠，需验证)
                - tool_execution: 工具执行 (可靠，取决于工具质量)
            source_content: 信息源内容（可选，用于更精细的评估）

        Returns:
            可靠性评分（0-100）
        """
        # 基础评分
        base_scores = {
            'knowledge_base': 95,   # 知识库最可靠
            'web_search': 80,       # 网页搜索较可靠
            'tool_execution': 85,   # 工具执行可靠
            'memory': 70,           # 历史记忆中等
            'model_inference': 60,  # 模型推理需验证
            'user_input': 50        # 用户输入需验证
        }

        score = base_scores.get(source_type, 50)

        # 根据内容进行微调
        if source_content:
            content_length = len(source_content)

            # 内容太短降低评分
            if content_length < 50:
                score -= 10
            # 内容适中增加评分
            elif content_length >= 500:
                score += 5
            elif content_length >= 1000:
                score += 10

            # 检查内容是否包含可疑标记
            suspicious_markers = ['广告', '推广', '赞助', 'sponsored', 'advertisement']
            for marker in suspicious_markers:
                if marker.lower() in source_content.lower():
                    score -= 15
                    break

            # 检查内容是否包含可信标记
            credibility_markers = ['研究', '报告', '论文', '官方', '研究', 'research', 'report', 'official']
            credibility_count = sum(1 for marker in credibility_markers if marker in source_content)
            if credibility_count >= 2:
                score += 10

        # 限制在0-100之间
        score = min(100, max(0, score))

        logger.debug(f"可靠性评分: source_type={source_type}, score={score}")
        return score

    def _calculate_authority_score(self, url: str, page_analysis: Dict) -> float:
        """
        计算权威性评分
        
        Args:
            url: URL
            page_analysis: 网页分析结果
            
        Returns:
            权威性评分（0-100）
        """
        score = 0
        
        # 基于URL域名的评分
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        authority_domains = self.config.get_quality_scoring_weights().get('authority', {})
        
        if 'gov' in domain or 'edu' in domain or 'org' in domain:
            score += 30  # 官方/教育/组织域名
        elif 'com' in domain or 'net' in domain:
            score += 20  # 商业域名
        elif 'cn' in domain:
            score += 15  # 中国域名
        else:
            score += 10  # 其他域名
        
        # 基于元数据的评分
        metadata = page_analysis.get('metadata', {})
        
        # 检查是否有作者信息
        if 'author' in metadata:
            score += 20
        
        # 检查是否有发布时间
        if 'publish_date' in metadata or 'date' in metadata:
            score += 15
        
        # 检查内容长度（较长的内容通常更权威）
        content_length = page_analysis.get('content_length', 0)
        if content_length >= 2000:
            score += 10
        elif content_length >= 1000:
            score += 5
        
        # 限制在0-100之间
        score = min(100, max(0, score))
        
        return score
    
    def _calculate_stability_score(self, page_analysis: Dict) -> float:
        """
        计算稳定性评分
        
        Args:
            page_analysis: 网页分析结果
            
        Returns:
            稳定性评分（0-100）
        """
        # 这里简化处理，实际应该基于历史数据
        # 如果能成功访问，给予基础分
        
        if not page_analysis['success']:
            return 0
        
        score = 50  # 基础分
        
        # 基于内容质量评分
        quality_score = page_analysis.get('quality_score', 0)
        score += min(30, quality_score * 0.3)
        
        # 基于广告占比（广告越少越稳定）
        ad_ratio = page_analysis.get('ad_ratio', 0)
        score -= ad_ratio * 20
        
        # 限制在0-100之间
        score = min(100, max(0, score))
        
        return score
    
    def _get_recommendation(self, is_quality: bool, should_cleanup: bool, ad_ratio: float) -> str:
        """
        生成评估建议
        
        Args:
            is_quality: 是否为优质源
            should_cleanup: 是否应该清理
            ad_ratio: 广告占比
            
        Returns:
            建议字符串
        """
        if should_cleanup:
            return "建议清理：不满足保留标准"
        elif is_quality:
            return "建议保留：优质信息源"
        elif ad_ratio > 0.3:
            return "建议观察：广告占比较高"
        else:
            return "建议保留：质量尚可"
    
    def _generate_evaluation_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成评估汇总报告
        
        Args:
            results: 评估结果列表
            
        Returns:
            汇总报告字典
        """
        total = len(results)
        successful = sum(1 for r in results if r['success'])
        
        if successful == 0:
            return {
                'total_count': total,
                'successful_count': successful,
                'failed_count': total - successful,
                'message': '没有成功评估的信息源'
            }
        
        successful_results = [r for r in results if r['success']]
        
        # 统计各类别
        high_quality = sum(1 for r in successful_results if r['quality_metrics']['is_high_quality'])
        should_cleanup = sum(1 for r in successful_results if r['evaluation']['should_cleanup'])
        high_ad = sum(1 for r in successful_results if r['ad_metrics']['exceeds_threshold'])
        
        # 平均评分
        avg_overall = sum(r['quality_metrics']['overall_score'] for r in successful_results) / len(successful_results)
        avg_ad_ratio = sum(r['ad_metrics']['ad_ratio'] for r in successful_results) / len(successful_results)
        
        summary = {
            'total_count': total,
            'successful_count': successful,
            'failed_count': total - successful,
            'statistics': {
                'high_quality_count': high_quality,
                'high_quality_rate': round(high_quality / successful * 100, 2),
                'cleanup_count': should_cleanup,
                'cleanup_rate': round(should_cleanup / successful * 100, 2),
                'high_ad_count': high_ad,
                'high_ad_rate': round(high_ad / successful * 100, 2)
            },
            'averages': {
                'overall_score': round(avg_overall, 2),
                'ad_ratio': round(avg_ad_ratio, 3)
            }
        }
        
        logger.info(f"评估汇总完成: {summary}")
        
        return summary


# 全局评估器实例
source_evaluator = SourceEvaluator()
