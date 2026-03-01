import logging
import httpx
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time

_search_cache = {}

@dataclass
class WebPageContent:
    """网页内容数据类"""
    url: str
    title: str
    content: str
    text_length: int
    html_length: int
    ad_ratio: float
    quality_score: float
    metadata: Dict[str, Any]

import webbrowser

def open_browser(url: str) -> str:
    """
    Open a URL in the system's default web browser.
    
    Args:
        url: The URL to open (e.g., 'https://www.google.com')
        
    Returns:
        Status message indicating success or failure.
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        webbrowser.open(url)
        return f"Successfully opened browser to: {url}"
    except Exception as e:
        return f"Error opening browser: {str(e)}"

def get_weather(location: str = "beijing") -> str:
    """Get current weather report for a location using wttr.in."""
    try:
        # Use wttr.in which returns plain text
        url = f"http://wttr.in/{location}?format=3" # Try HTTP first
        # Increased timeout to 30s for better stability
        # Disable SSL verify to avoid handshake errors
        with httpx.Client(timeout=30.0, verify=False, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "curl/7.68.0"})
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"Error: Failed to get weather (Status {response.status_code})"
    except Exception as e:
        return f"Error getting weather: {str(e)}"

def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for information using Baidu (国内网络环境可用).
    """
    global _search_cache
    
    # 1. Check Cache
    cache_key = f"{query}::{max_results}"
    if cache_key in _search_cache:
        return f"(Cached) {_search_cache[cache_key]}"

    try:
        # 2. Baidu Search Logic
        results = []
        
        # 请求头模拟真实浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "https://www.baidu.com/"
        }
        
        url = "https://www.baidu.com/s"
        params = {"wd": query, "rn": max_results + 10} # rn参数指定返回结果数量
        
        with httpx.Client(timeout=30.0, verify=False, follow_redirects=True, headers=headers) as client:
            response = client.get(url, params=params)
            
            if response.status_code != 200:
                return f"Error: Baidu search failed with status {response.status_code}"
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 百度搜索结果解析
            search_items = soup.select("div.result.c-container, div.result-op.c-container")
            
            # 兜底选择器
            if not search_items:
                search_items = soup.select("div[class*='result']")
            
            for item in search_items:
                if len(results) >= max_results:
                    break
                    
                try:
                    # 提取标题和链接
                    title_tag = item.find("h3")
                    if not title_tag: continue
                    link_tag = title_tag.find("a")
                    if not link_tag: continue
                    
                    title = title_tag.get_text().strip()
                    href = str(link_tag.get("href", ""))
                    if not href or href.startswith("/s?"): continue
                    
                    # 提取摘要
                    snippet = ""
                    # 优先找摘要容器
                    content_tags = [
                        item.find("div", class_="c-abstract"),
                        item.find("div", class_="c-span-last"),
                        item.find("span", class_="content-right_8Zs40"),
                        item.find("div", class_="c-line-clamp2")
                    ]
                    for tag in content_tags:
                        if tag:
                            snippet = tag.get_text().strip()
                            break
                    
                    if not snippet:
                        # 兜底查找所有p标签的内容
                        p_tags = item.find_all("p")
                        snippet = " ".join([p.get_text().strip() for p in p_tags])[:200]
                    
                    if title and href:
                        results.append({
                            "title": title,
                            "href": href,
                            "body": snippet if snippet else "无摘要"
                        })
                except Exception as e:
                    logging.warning(f"解析百度搜索结果失败: {str(e)}")
                    continue
        
        if not results:
            return "No results found on Baidu."
        
        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"{i}. [{r['title']}]({r['href']})\n   {r['body']}")
        
        output = "\n\n".join(formatted)
        
        # 3. Update Cache
        if len(_search_cache) > 100:
            _search_cache.clear()
        _search_cache[cache_key] = output
        
        return output
        
    except Exception as e:
        logging.error(f"Bing search unexpected error: {str(e)}, query: {query}")
        return f"Error searching web: {str(e)}"


# ============================================
# 网页内容爬取功能
# ============================================

def crawl_webpage(url: str, timeout: int = 30, max_retries: int = 3) -> Optional[WebPageContent]:
    """
    爬取网页内容并分析
    
    Args:
        url: 要爬取的网页URL
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        
    Returns:
        WebPageContent 对象，包含网页内容和分析结果
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=timeout, verify=False, follow_redirects=True, headers=headers) as client:
                response = client.get(url)
                
                if response.status_code != 200:
                    logging.warning(f"Failed to fetch {url}: status {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # 指数退避
                        continue
                    return None
                
                html_content = response.text
                html_length = len(html_content)
                
                # 使用BeautifulSoup解析
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取标题
                title = ""
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
                
                # 提取正文内容
                content = extract_main_content(soup)
                text_length = len(content)
                
                # 识别广告占比
                ad_ratio = detect_ad_ratio(soup, content, html_content)
                
                # 评估内容专业度
                quality_score = evaluate_content_quality(title, content, soup)
                
                # 提取元数据
                metadata = extract_metadata(soup)
                
                return WebPageContent(
                    url=url,
                    title=title,
                    content=content,
                    text_length=text_length,
                    html_length=html_length,
                    ad_ratio=ad_ratio,
                    quality_score=quality_score,
                    metadata=metadata
                )
                
        except Exception as e:
            logging.error(f"Error crawling {url} (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
    
    return None


def extract_main_content(soup: BeautifulSoup) -> str:
    """
    提取网页主要内容
    
    Args:
        soup: BeautifulSoup对象
        
    Returns:
        提取的正文文本
    """
    # 移除不需要的标签
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
        tag.decompose()
    
    # 尝试找到主要内容区域
    main_content_selectors = [
        'article',
        'main',
        '[role="main"]',
        '.content',
        '.article-content',
        '.post-content',
        '.entry-content',
        '#content',
        '#main-content'
    ]
    
    for selector in main_content_selectors:
        main = soup.select_one(selector)
        if main:
            return main.get_text(separator='\n', strip=True)
    
    # 如果没找到主要内容区域，提取所有段落
    paragraphs = soup.find_all('p')
    content = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    
    return content


def extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    提取网页元数据
    
    Args:
        soup: BeautifulSoup对象
        
    Returns:
        元数据字典
    """
    metadata = {}
    
    # 提取meta标签
    meta_tags = soup.find_all('meta')
    for meta in meta_tags:
        name = meta.get('name') or meta.get('property')
        content = meta.get('content')
        if name and content:
            metadata[name] = content
    
    # 提取发布时间
    date_selectors = [
        'time[datetime]',
        '.publish-time',
        '.date',
        '.post-date',
        '[class*="time"]',
        '[class*="date"]'
    ]
    
    for selector in date_selectors:
        time_tag = soup.select_one(selector)
        if time_tag:
            metadata['publish_date'] = time_tag.get('datetime') or time_tag.get_text(strip=True)
            break
    
    # 提取作者
    author_selectors = [
        '.author',
        '.post-author',
        '[class*="author"]',
        'meta[name="author"]'
    ]
    
    for selector in author_selectors:
        if selector.startswith('meta'):
            author_tag = soup.select_one(selector)
            if author_tag:
                metadata['author'] = author_tag.get('content')
                break
        else:
            author_tag = soup.select_one(selector)
            if author_tag:
                metadata['author'] = author_tag.get_text(strip=True)
                break
    
    return metadata


# ============================================
# 广告占比识别功能
# ============================================

def detect_ad_ratio(soup: BeautifulSoup, content: str, html_content: str) -> float:
    """
    检测网页中的广告占比
    
    Args:
        soup: BeautifulSoup对象
        content: 提取的正文内容
        html_content: 原始HTML内容
        
    Returns:
        广告占比（0-1之间的浮点数）
    """
    total_ad_elements = 0
    total_content_elements = 0
    
    # 广告关键词和选择器
    ad_keywords = ['ad', 'advertisement', 'sponsored', 'sponsor', '推广', '广告']
    ad_selectors = [
        '[class*="ad"]',
        '[id*="ad"]',
        '[class*="advertisement"]',
        '[class*="sponsored"]',
        '[class*="推广"]',
        '[class*="广告"]',
        'iframe[src*="ad"]',
        'iframe[src*="google"]',
        'iframe[src*="doubleclick"]'
    ]
    
    # 1. 统计广告元素
    for selector in ad_selectors:
        ad_elements = soup.select(selector)
        total_ad_elements += len(ad_elements)
    
    # 2. 检测文本中的广告关键词
    for keyword in ad_keywords:
        # 检查class和id属性
        elements_with_keyword = soup.find_all(attrs={
            'class': re.compile(keyword, re.IGNORECASE),
            'id': re.compile(keyword, re.IGNORECASE)
        })
        total_ad_elements += len(elements_with_keyword)
        
        # 检查链接中的广告关键词
        ad_links = soup.find_all('a', string=re.compile(keyword, re.IGNORECASE))
        total_ad_elements += len(ad_links)
    
    # 3. 统计内容元素
    content_selectors = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'main']
    for selector in content_selectors:
        content_elements = soup.select(selector)
        total_content_elements += len(content_elements)
    
    # 4. 统计可疑的外部链接（广告链接）
    suspicious_domains = [
        'doubleclick.net',
        'googleadservices.com',
        'googlesyndication.com',
        'advertising.com',
        'googleads.g.doubleclick.net'
    ]
    
    all_links = soup.find_all('a', href=True)
    suspicious_links = [
        link for link in all_links
        if any(domain in link['href'] for domain in suspicious_domains)
    ]
    total_ad_elements += len(suspicious_links)
    
    # 5. 计算广告占比
    total_elements = total_ad_elements + total_content_elements
    
    if total_elements == 0:
        return 0.0
    
    ad_ratio = total_ad_elements / total_elements
    
    # 考虑文本长度因素：如果正文很短但有很多广告元素，提高广告占比
    if total_content_elements > 0:
        text_ratio = total_ad_elements / total_content_elements
        ad_ratio = max(ad_ratio, text_ratio * 0.5)  # 取较大值
    
    # 限制在0-1之间
    ad_ratio = min(1.0, max(0.0, ad_ratio))
    
    return round(ad_ratio, 3)


# ============================================
# 内容专业度评分功能
# ============================================

def evaluate_content_quality(title: str, content: str, soup: BeautifulSoup) -> float:
    """
    评估内容专业度
    
    Args:
        title: 网页标题
        content: 正文内容
        soup: BeautifulSoup对象
        
    Returns:
        专业度评分（0-100）
    """
    scores = {
        'length': 0,      # 内容长度得分
        'structure': 0,   # 结构完整性得分
        'professional': 0, # 专业性得分
        'readability': 0, # 可读性得分
        'authority': 0    # 权威性得分
    }
    
    # 1. 内容长度评分（0-20分）
    content_length = len(content)
    if content_length >= 2000:
        scores['length'] = 20
    elif content_length >= 1000:
        scores['length'] = 15
    elif content_length >= 500:
        scores['length'] = 10
    elif content_length >= 200:
        scores['length'] = 5
    else:
        scores['length'] = 2
    
    # 2. 结构完整性评分（0-20分）
    has_title = len(title) > 0
    has_paragraphs = len(soup.find_all('p')) >= 3
    has_headings = len(soup.find_all(['h1', 'h2', 'h3'])) >= 1
    has_lists = len(soup.find_all(['ul', 'ol'])) >= 1
    
    structure_score = 0
    if has_title:
        structure_score += 5
    if has_paragraphs:
        structure_score += 5
    if has_headings:
        structure_score += 5
    if has_lists:
        structure_score += 5
    
    scores['structure'] = structure_score
    
    # 3. 专业性评分（0-30分）
    professional_keywords = [
        '研究', '分析', '报告', '数据', '统计', '实验', '结论',
        '研究', 'research', 'analysis', 'report', 'data', 'statistics',
        'experiment', 'conclusion', 'methodology', 'method', '方法'
    ]
    
    content_lower = content.lower()
    title_lower = title.lower()
    
    keyword_count = 0
    for keyword in professional_keywords:
        if keyword.lower() in content_lower or keyword.lower() in title_lower:
            keyword_count += 1
    
    # 检查是否有数字和图表引用
    has_numbers = bool(re.search(r'\d+[%。，.、]', content))
    has_references = bool(re.search(r'\[\d+\]|\(\d+\)|参考文献|引用|reference', content_lower))
    
    professional_score = min(30, (keyword_count * 5) + (10 if has_numbers else 0) + (10 if has_references else 0))
    scores['professional'] = professional_score
    
    # 4. 可读性评分（0-15分）
    sentences = re.split(r'[。！？.!?]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) >= 5:
        # 计算平均句子长度
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        # 理想的句子长度在30-100字符之间
        if 30 <= avg_sentence_length <= 100:
            readability_score = 15
        elif 20 <= avg_sentence_length <= 150:
            readability_score = 10
        else:
            readability_score = 5
    else:
        readability_score = 2
    
    scores['readability'] = readability_score
    
    # 5. 权威性评分（0-15分）
    domain = urlparse(soup.find('link', rel='canonical') and soup.find('link', rel='canonical').get('href') or '').netloc
    
    # 检查是否为权威域名
    authority_domains = ['.gov.cn', '.gov', '.edu.cn', '.edu', '.org']
    has_authority_domain = any(domain in domain for domain in authority_domains) if domain else False
    
    # 检查是否有作者信息
    has_author = bool(soup.find(attrs={'class': re.compile('author', re.IGNORECASE)}))
    
    # 检查是否有发布时间
    has_date = bool(soup.find('time') or soup.find(attrs={'class': re.compile('date|time', re.IGNORECASE)}))
    
    authority_score = (5 if has_authority_domain else 0) + (5 if has_author else 0) + (5 if has_date else 0)
    scores['authority'] = authority_score
    
    # 计算总分
    total_score = sum(scores.values())
    
    # 限制在0-100之间
    total_score = min(100, max(0, total_score))
    
    return round(total_score, 2)


# ============================================
# 批量网页分析功能
# ============================================

def analyze_webpage(url: str) -> Dict[str, Any]:
    """
    分析单个网页的综合信息
    
    Args:
        url: 网页URL
        
    Returns:
        包含网页分析结果的字典
    """
    try:
        page_content = crawl_webpage(url)
        
        if not page_content:
            return {
                'url': url,
                'success': False,
                'error': 'Failed to crawl webpage'
            }
        
        return {
            'url': url,
            'success': True,
            'title': page_content.title,
            'content_length': page_content.text_length,
            'ad_ratio': page_content.ad_ratio,
            'quality_score': page_content.quality_score,
            'metadata': page_content.metadata,
            'content_preview': page_content.content[:200] + '...' if len(page_content.content) > 200 else page_content.content
        }
        
    except Exception as e:
        logging.error(f"Error analyzing webpage {url}: {str(e)}")
        return {
            'url': url,
            'success': False,
            'error': str(e)
        }


def batch_analyze_webpages(urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
    """
    批量分析多个网页
    
    Args:
        urls: 网页URL列表
        delay: 请求之间的延迟（秒）
        
    Returns:
        网页分析结果列表
    """
    results = []
    
    for i, url in enumerate(urls):
        logging.info(f"Analyzing webpage {i+1}/{len(urls)}: {url}")
        
        result = analyze_webpage(url)
        results.append(result)
        
        # 添加延迟避免请求过快
        if i < len(urls) - 1:
            time.sleep(delay)
    
    return results

