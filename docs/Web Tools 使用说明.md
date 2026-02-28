# Web Tools 使用说明

## 概述

Web Tools 模块提供了完整的网页内容爬取、广告识别和内容质量评分功能，支持信息源的自动化评估和筛选。

## 核心功能

### 1. 网页内容爬取

自动爬取网页内容并提取关键信息：

- **功能**：爬取网页标题、正文、元数据
- **特性**：
  - 智能提取主要内容区域
  - 自动移除无关标签（script、style、nav等）
  - 支持重试机制（最多3次）
  - 超时保护（默认30秒）

### 2. 广告占比识别

检测网页中的广告元素并计算广告占比：

- **检测方式**：
  - CSS选择器匹配（class/id包含ad关键词）
  - 文本关键词识别
  - 可疑外部链接检测
  - iframe广告检测
- **返回值**：0-1之间的浮点数（广告占比）

### 3. 内容专业度评分

多维度评估内容质量：

- **评分维度**（总分100分）：
  - 内容长度（0-20分）
  - 结构完整性（0-20分）
  - 专业性（0-30分）
  - 可读性（0-15分）
  - 权威性（0-15分）

### 4. 信息源评估流程

集成爬取、分类、评分等功能，完成信息源综合评估：

- **评估指标**：
  - 自动分类（5种分类标签）
  - 权威性评分
  - 稳定性评分
  - 内容质量评分
  - 综合评分
  - 广告占比
  - 保留/清理建议

## API 参考

### 核心函数

#### crawl_webpage()

爬取单个网页内容

```python
from src.tools.web_tools import crawl_webpage

page = crawl_webpage(url="https://example.com", timeout=30, max_retries=3)

if page:
    print(f"标题: {page.title}")
    print(f"内容: {page.content}")
    print(f"广告占比: {page.ad_ratio}")
    print(f"质量评分: {page.quality_score}")
```

**参数**：
- `url`: 要爬取的网页URL
- `timeout`: 请求超时时间（秒），默认30
- `max_retries`: 最大重试次数，默认3

**返回**：`WebPageContent` 对象或 `None`

#### analyze_webpage()

分析单个网页的综合信息

```python
from src.tools.web_tools import analyze_webpage

result = analyze_webpage(url="https://example.com")

if result['success']:
    print(f"标题: {result['title']}")
    print(f"内容长度: {result['content_length']}")
    print(f"广告占比: {result['ad_ratio']}")
    print(f"质量评分: {result['quality_score']}")
```

**参数**：
- `url`: 网页URL

**返回**：包含分析结果的字典

#### batch_analyze_webpages()

批量分析多个网页

```python
from src.tools.web_tools import batch_analyze_webpages

urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

results = batch_analyze_webpages(urls, delay=1.0)

for result in results:
    if result['success']:
        print(f"{result['url']}: {result['quality_score']}/100")
```

**参数**：
- `urls`: 网页URL列表
- `delay`: 请求之间的延迟（秒），默认1.0

**返回**：网页分析结果列表

### 信息源评估器

#### SourceEvaluator 类

完成信息源的综合评估

```python
from src.utils.source_evaluator import source_evaluator

# 评估单个信息源
result = source_evaluator.evaluate_single_source(url="https://example.com")

if result['success']:
    print(f"分类: {result['classification']['category']}")
    print(f"综合评分: {result['quality_metrics']['overall_score']}")
    print(f"是否优质: {result['quality_metrics']['is_high_quality']}")
    print(f"建议: {result['evaluation']['recommendation']}")

# 批量评估多个信息源
urls = ["https://example.com/1", "https://example.com/2"]
results = source_evaluator.evaluate_multiple_sources(urls, delay=1.0)
```

## 使用示例

### 示例1：单个网页分析

```python
from src.tools.web_tools import crawl_webpage

# 爬取网页
page = crawl_webpage("https://www.example.com")

if page:
    print(f"标题: {page.title}")
    print(f"内容长度: {page.text_length} 字符")
    print(f"HTML长度: {page.html_length} 字符")
    print(f"广告占比: {page.ad_ratio*100:.2f}%")
    print(f"质量评分: {page.quality_score}/100")
    
    # 显示元数据
    for key, value in page.metadata.items():
        print(f"  {key}: {value}")
```

### 示例2：广告检测

```python
from src.tools.web_tools import detect_ad_ratio
from bs4 import BeautifulSoup

html_content = """
<html>
<body>
    <div class="advertisement">这是广告</div>
    <div class="content">
        <h1>文章标题</h1>
        <p>正文内容...</p>
    </div>
</body>
</html>
"""

soup = BeautifulSoup(html_content, 'html.parser')
content = soup.get_text()
ad_ratio = detect_ad_ratio(soup, content, html_content)

print(f"广告占比: {ad_ratio*100:.2f}%")

if ad_ratio > 0.25:
    print("⚠️ 广告占比过高")
```

### 示例3：内容质量评分

```python
from src.tools.web_tools import evaluate_content_quality
from bs4 import BeautifulSoup

html_content = """
<html>
<body>
    <article>
        <h1>2024年经济发展研究报告</h1>
        <p class="author">张三教授</p>
        <time datetime="2024-02-28">2024年2月28日</time>
        <h2>研究方法</h2>
        <p>本研究采用定量分析方法。根据统计数据[1]，GDP增长率为5.2%。</p>
        <ul>
            <li>制造业增长6.5%</li>
            <li>服务业增长4.8%</li>
        </ul>
    </article>
</body>
</html>
"""

soup = BeautifulSoup(html_content, 'html.parser')
title = "2024年经济发展研究报告"
content = soup.get_text()

quality_score = evaluate_content_quality(title, content, soup)

print(f"内容质量评分: {quality_score}/100")

if quality_score > 70:
    print("✓ 高质量内容")
elif quality_score > 50:
    print("○ 中等质量内容")
else:
    print("✗ 低质量内容")
```

### 示例4：信息源评估

```python
from src.utils.source_evaluator import source_evaluator

# 评估单个信息源
result = source_evaluator.evaluate_single_source("https://news.example.com/article123")

if result['success']:
    print("=" * 60)
    print("信息源评估报告")
    print("=" * 60)
    
    # 基本信息
    print(f"\n【基本信息】")
    print(f"URL: {result['url']}")
    print(f"标题: {result['content_info']['title']}")
    print(f"评估时间: {result['evaluation_time']}")
    
    # 分类信息
    print(f"\n【分类信息】")
    print(f"分类: {result['classification']['category']}")
    print(f"自动分类: {'是' if result['classification']['auto_classified'] else '否'}")
    
    # 质量指标
    print(f"\n【质量指标】")
    print(f"权威性评分: {result['quality_metrics']['authority_score']}/100")
    print(f"稳定性评分: {result['quality_metrics']['stability_score']}/100")
    print(f"内容质量评分: {result['quality_metrics']['content_score']}/100")
    print(f"综合评分: {result['quality_metrics']['overall_score']}/100")
    print(f"是否优质源: {'是' if result['quality_metrics']['is_high_quality'] else '否'}")
    
    # 广告指标
    print(f"\n【广告指标】")
    print(f"广告占比: {result['ad_metrics']['ad_ratio']*100:.2f}%")
    print(f"是否超标: {'是' if result['ad_metrics']['exceeds_threshold'] else '否'}")
    
    # 评估建议
    print(f"\n【评估建议】")
    print(f"是否应该清理: {'是' if result['evaluation']['should_cleanup'] else '否'}")
    print(f"清理原因: {result['evaluation']['cleanup_reason']}")
    print(f"建议: {result['evaluation']['recommendation']}")

# 批量评估
urls = [
    "https://example.com/news1",
    "https://example.com/news2",
    "https://example.com/news3"
]

print("\n批量评估信息源...")
results = source_evaluator.evaluate_multiple_sources(urls, delay=2.0)

print(f"\n评估汇总:")
for i, result in enumerate(results, 1):
    if result['success']:
        status = "✓" if result['quality_metrics']['is_high_quality'] else "○"
        print(f"{status} {i}. {result['content_info']['title']}")
        print(f"   综合评分: {result['quality_metrics']['overall_score']}/100")
        print(f"   广告占比: {result['ad_metrics']['ad_ratio']*100:.2f}%")
        print(f"   建议: {result['evaluation']['recommendation']}")
```

## 配置

Web Tools 的行为可以通过配置文件调整：

### 筛选阈值配置

在 `src/config/config.yaml` 中：

```yaml
screening_criteria:
  quality_source_threshold:
    min_authority_score: 60
    min_stability_score: 50
    min_content_score: 55
    min_overall_score: 65
    max_ad_ratio: 0.25
```

### 广告识别配置

```yaml
screening_criteria:
  ad_detection:
    ad_density_threshold: 0.3
    suspicious_keywords:
      - "广告"
      - "赞助"
      - "推广"
```

## 测试

运行功能测试：

```bash
cd /workspace/projects
python test_web_tools.py
```

测试覆盖：
- ✓ 网页内容爬取
- ✓ 广告占比识别
- ✓ 内容质量评分
- ✓ 网页综合分析
- ✓ 批量网页分析

## 性能优化

### 请求延迟

批量分析时设置适当的延迟，避免请求过快：

```python
results = batch_analyze_webpages(urls, delay=2.0)  # 每次请求间隔2秒
```

### 超时设置

根据网络情况调整超时时间：

```python
page = crawl_webpage(url, timeout=60)  # 超时时间设为60秒
```

### 重试机制

系统内置最多3次重试，使用指数退避策略：

```python
page = crawl_webpage(url, max_retries=5)  # 最多重试5次
```

## 注意事项

1. **网络依赖**：需要稳定的网络连接
2. **请求频率**：批量分析时注意控制请求频率，避免被目标网站封禁
3. **内容过滤**：某些网站可能有反爬机制，建议设置合理的User-Agent
4. **编码问题**：确保正确处理各种字符编码（UTF-8、GBK等）
5. **法律合规**：使用爬虫功能时请遵守目标网站的robots.txt和相关法律法规

## 常见问题

### Q: 如何处理访问被拒绝的网页？

A: 可以调整请求头、增加重试次数、使用代理等方式。代码已内置重试机制和模拟浏览器User-Agent。

### Q: 广告识别准确吗？

A: 广告识别基于多种策略，但可能存在误判。建议结合人工审核。

### Q: 如何提高内容质量评分的准确性？

A: 可以调整评分权重配置，或根据特定领域的特点定制评分规则。

### Q: 批量分析会占用大量资源吗？

A: 批量分析设置了延迟保护机制，建议根据硬件性能调整并发数量和延迟时间。

## 版本历史

- **v2.0** (2026-02-28)
  - 新增网页内容爬取功能
  - 新增广告占比识别功能
  - 新增内容专业度评分功能
  - 新增信息源评估流程集成
  - 通过全部功能测试（5/5）

- **v1.0** (初始版本)
  - 实现天气查询功能
  - 实现网络搜索功能
