#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Tools模块单元测试用例
"""
import pytest
from bs4 import BeautifulSoup
from src.tools.web_tools import detect_ad_ratio, evaluate_content_quality, analyze_webpage, batch_analyze_webpages


class TestWebTools:
    """Web Tools模块测试类"""

    def test_detect_ad_ratio_normal_case(self):
        """测试正常网页的广告占比计算"""
        html = """
        <html>
            <body>
                <div class="ad">这是一个广告，内容很长很长很长很长很长很长很长</div>
                <article>
                    <h1>测试文章标题</h1>
                    <p>这是正文第一段，内容长度足够</p>
                    <p>这是正文第二段，内容长度足够</p>
                    <p>这是正文第三段，内容长度足够</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = "测试文章标题 这是正文第一段，内容长度足够 这是正文第二段，内容长度足够 这是正文第三段，内容长度足够"
        ad_ratio = detect_ad_ratio(soup, content, html)
        assert 0.0 <= ad_ratio <= 1.0
        # 广告长度明显小于正文长度，占比应该小于0.5
        assert ad_ratio < 0.5

    def test_detect_ad_ratio_mostly_ad(self):
        """测试大部分内容是广告的网页"""
        html = """
        <html>
            <body>
                <div class="ad">广告内容1很长很长很长很长很长很长很长很长很长</div>
                <div class="ad">广告内容2很长很长很长很长很长很长很长很长很长</div>
                <div class="ad">广告内容3很长很长很长很长很长很长很长很长很长</div>
                <p>少量正文内容</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = "少量正文内容"
        ad_ratio = detect_ad_ratio(soup, content, html)
        assert 0.0 <= ad_ratio <= 1.0
        # 广告占比应该大于0.7
        assert ad_ratio > 0.7

    def test_detect_ad_ratio_no_ad(self):
        """测试没有广告的网页"""
        html = """
        <html>
            <body>
                <article>
                    <h1>无广告文章标题</h1>
                    <p>正文第一段</p>
                    <p>正文第二段</p>
                    <p>正文第三段</p>
                    <p>正文第四段</p>
                </article>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        content = "无广告文章标题 正文第一段 正文第二段 正文第三段 正文第四段"
        ad_ratio = detect_ad_ratio(soup, content, html)
        assert ad_ratio == 0.0

    def test_evaluate_content_quality_no_repeat_keyword(self):
        """测试专业关键词不重复加分的情况"""
        title = "人工智能研究报告"
        # 同一个关键词"研究"重复出现多次
        content = "本研究针对人工智能领域进行研究，通过大量研究数据得出研究结论。"
        html = """
        <html>
            <body>
                <h1>人工智能研究报告</h1>
                <p>本研究针对人工智能领域进行研究，通过大量研究数据得出研究结论。</p>
                <p>包含数字：12345</p>
            </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        score = evaluate_content_quality(title, content, soup)
        # 专业性评分最多30分，同一个关键词重复出现不应该重复加分，所以分数不会过高
        professional_score = score if isinstance(score, (int, float)) else score.get('professional', 0)
        assert professional_score <= 30
        # 虽然"研究"重复了4次，但只应该算1次匹配
        assert professional_score < 25

    def test_analyze_webpage_empty_url(self):
        """测试传入空URL的参数校验"""
        result = analyze_webpage("")
        assert result['success'] == False
        assert 'error' in result

    def test_analyze_webpage_invalid_url(self):
        """测试传入无效URL的参数校验"""
        result = analyze_webpage("not_a_valid_url")
        assert result['success'] == False
        assert 'error' in result

    def test_batch_analyze_webpages_empty_list(self):
        """测试传入空URL列表的参数校验"""
        results = batch_analyze_webpages([])
        assert len(results) == 0

    def test_batch_analyze_webpages_invalid_urls(self):
        """测试传入包含无效URL的列表"""
        urls = ["", "not_a_valid_url", "https://www.baidu.com"]
        results = batch_analyze_webpages(urls, delay=0.1)
        assert len(results) == 3
        assert results[0]['success'] == False
        assert results[1]['success'] == False
        # 第三个有效URL应该正常返回（网络正常的情况下）
        assert 'success' in results[2]
