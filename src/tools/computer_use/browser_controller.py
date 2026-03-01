"""
AI 电脑操作员系统 - 浏览器操作模块
通过 Playwright 控制浏览器
"""
import asyncio
import base64
import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = Browser = BrowserContext = None


@dataclass
class BrowserSession:
    """浏览器会话"""
    browser: Browser
    context: BrowserContext
    page: Page
    session_id: str


class BrowserController:
    """
    浏览器控制器
    控制浏览器进行网页操作
    """
    
    def __init__(self, headless: bool = False, screenshot_dir: str = "workspace/browser_screenshots"):
        """
        初始化浏览器控制器
        
        Args:
            headless: 是否无头模式（不显示浏览器窗口）
            screenshot_dir: 截图保存目录
        """
        self.logger = logging.getLogger(__name__)
        
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("需要安装 playwright: pip install playwright && playwright install")
        
        self.headless = headless
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        self.logger.info("浏览器控制器初始化完成")
    
    async def start(self, browser_type: str = "chromium") -> Page:
        """
        启动浏览器
        
        Args:
            browser_type: 浏览器类型 (chromium, firefox, webkit)
            
        Returns:
            Page 对象
        """
        try:
            self._playwright = await async_playwright().start()
            
            # 选择浏览器
            if browser_type == "chromium":
                browser_launcher = self._playwright.chromium
            elif browser_type == "firefox":
                browser_launcher = self._playwright.firefox
            elif browser_type == "webkit":
                browser_launcher = self._playwright.webkit
            else:
                browser_launcher = self._playwright.chromium
            
            # 启动浏览器
            self._browser = await browser_launcher.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # 创建上下文
            self._context = await self._browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir=str(self.screenshot_dir / "videos") if not self.headless else None
            )
            
            # 创建页面
            self._page = await self._context.new_page()
            
            self.logger.info(f"浏览器启动成功: {browser_type}")
            return self._page
            
        except Exception as e:
            self.logger.error(f"浏览器启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """关闭浏览器"""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.error(f"关闭浏览器失败: {e}")
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """
        导航到指定URL
        
        Args:
            url: 目标网址
            wait_until: 等待条件 (load, domcontentloaded, networkidle)
        """
        if not self._page:
            raise RuntimeError("浏览器未启动，请先调用 start()")
        
        try:
            await self._page.goto(url, wait_until=wait_until)
            self.logger.info(f"导航到: {url}")
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            raise
    
    async def click(self, selector: str, timeout: int = 5000) -> None:
        """
        点击元素
        
        Args:
            selector: CSS选择器或XPath
            timeout: 超时时间（毫秒）
        """
        try:
            await self._page.click(selector, timeout=timeout)
            self.logger.debug(f"点击元素: {selector}")
        except Exception as e:
            self.logger.error(f"点击失败 {selector}: {e}")
            raise
    
    async def fill(self, selector: str, text: str, timeout: int = 5000) -> None:
        """
        填充输入框
        
        Args:
            selector: CSS选择器
            text: 要输入的文本
            timeout: 超时时间
        """
        try:
            await self._page.fill(selector, text, timeout=timeout)
            self.logger.debug(f"填充输入框 {selector}: {text[:20]}...")
        except Exception as e:
            self.logger.error(f"填充失败 {selector}: {e}")
            raise
    
    async def type_text(self, selector: str, text: str, delay: int = 50) -> None:
        """
        模拟打字输入
        
        Args:
            selector: CSS选择器
            text: 要输入的文本
            delay: 按键间隔（毫秒）
        """
        try:
            await self._page.type(selector, text, delay=delay)
            self.logger.debug(f"打字输入 {selector}: {text[:20]}...")
        except Exception as e:
            self.logger.error(f"输入失败 {selector}: {e}")
            raise
    
    async def press_key(self, key: str) -> None:
        """
        按下键盘按键
        
        Args:
            key: 按键名称 (Enter, Tab, Escape, etc.)
        """
        try:
            await self._page.keyboard.press(key)
            self.logger.debug(f"按键: {key}")
        except Exception as e:
            self.logger.error(f"按键失败: {e}")
            raise
    
    async def screenshot(self, full_page: bool = False, 
                        selector: Optional[str] = None) -> str:
        """
        截图
        
        Args:
            full_page: 是否截取完整页面
            selector: 只截取特定元素
            
        Returns:
            base64 编码的截图
        """
        try:
            if selector:
                element = await self._page.query_selector(selector)
                if element:
                    screenshot_bytes = await element.screenshot()
                else:
                    raise ValueError(f"元素未找到: {selector}")
            else:
                screenshot_bytes = await self._page.screenshot(full_page=full_page)
            
            return base64.b64encode(screenshot_bytes).decode()
            
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            raise
    
    async def get_text(self, selector: str) -> str:
        """
        获取元素文本
        
        Args:
            selector: CSS选择器
            
        Returns:
            元素文本内容
        """
        try:
            element = await self._page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text or ""
            return ""
        except Exception as e:
            self.logger.error(f"获取文本失败 {selector}: {e}")
            return ""
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        获取元素属性
        
        Args:
            selector: CSS选择器
            attribute: 属性名
            
        Returns:
            属性值
        """
        try:
            element = await self._page.query_selector(selector)
            if element:
                return await element.get_attribute(attribute)
            return None
        except Exception as e:
            self.logger.error(f"获取属性失败 {selector}: {e}")
            return None
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> None:
        """
        等待元素出现
        
        Args:
            selector: CSS选择器
            timeout: 超时时间
        """
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
        except Exception as e:
            self.logger.error(f"等待元素超时 {selector}: {e}")
            raise
    
    async def wait_for_load_state(self, state: str = "networkidle") -> None:
        """
        等待页面加载状态
        
        Args:
            state: load, domcontentloaded, networkidle
        """
        await self._page.wait_for_load_state(state)
    
    async def scroll_down(self, amount: int = 500) -> None:
        """向下滚动"""
        await self._page.evaluate(f"window.scrollBy(0, {amount})")
    
    async def scroll_up(self, amount: int = 500) -> None:
        """向上滚动"""
        await self._page.evaluate(f"window.scrollBy(0, -{amount})")
    
    async def scroll_to_element(self, selector: str) -> None:
        """滚动到元素"""
        element = await self._page.query_selector(selector)
        if element:
            await element.scroll_into_view_if_needed()
    
    async def get_url(self) -> str:
        """获取当前URL"""
        return self._page.url
    
    async def get_title(self) -> str:
        """获取页面标题"""
        return await self._page.title()
    
    async def go_back(self) -> None:
        """后退"""
        await self._page.go_back()
    
    async def go_forward(self) -> None:
        """前进"""
        await self._page.go_forward()
    
    async def reload(self) -> None:
        """刷新页面"""
        await self._page.reload()
    
    async def evaluate(self, script: str) -> Any:
        """
        执行 JavaScript
        
        Args:
            script: JavaScript 代码
            
        Returns:
            执行结果
        """
        return await self._page.evaluate(script)
    
    async def find_elements(self, selector: str) -> List[Dict[str, Any]]:
        """
        查找所有匹配的元素
        
        Args:
            selector: CSS选择器
            
        Returns:
            元素信息列表
        """
        elements = await self._page.query_selector_all(selector)
        results = []
        for i, elem in enumerate(elements):
            try:
                text = await elem.text_content()
                visible = await elem.is_visible()
                results.append({
                    "index": i,
                    "text": text[:100] if text else "",
                    "visible": visible
                })
            except:
                pass
        return results
    
    async def close_popup(self) -> None:
        """关闭弹窗（按 Escape 键）"""
        await self.press_key("Escape")
    
    async def accept_dialog(self) -> None:
        """接受对话框（确定）"""
        await self.press_key("Enter")
    
    async def dismiss_dialog(self) -> None:
        """取消对话框"""
        await self.press_key("Escape")
    
    async def switch_to_tab(self, index: int = 0) -> None:
        """
        切换到指定标签页
        
        Args:
            index: 标签页索引
        """
        pages = self._context.pages
        if 0 <= index < len(pages):
            self._page = pages[index]
            await self._page.bring_to_front()
    
    async def new_tab(self, url: Optional[str] = None) -> Page:
        """
        打开新标签页
        
        Args:
            url: 可选的初始URL
            
        Returns:
            新页面
        """
        self._page = await self._context.new_page()
        if url:
            await self.navigate(url)
        return self._page
    
    async def close_tab(self) -> None:
        """关闭当前标签页"""
        await self._page.close()
        # 切换到第一个可用标签页
        if self._context.pages:
            self._page = self._context.pages[0]


# 同步包装器（方便非异步代码使用）
class SyncBrowserController:
    """同步浏览器控制器包装器"""
    
    def __init__(self, headless: bool = False):
        self._async_controller = BrowserController(headless=headless)
        self._loop = None
    
    def _run(self, coro):
        """运行异步协程"""
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)
    
    def start(self, browser_type: str = "chromium"):
        return self._run(self._async_controller.start(browser_type))
    
    def stop(self):
        return self._run(self._async_controller.stop())
    
    def navigate(self, url: str):
        return self._run(self._async_controller.navigate(url))
    
    def click(self, selector: str):
        return self._run(self._async_controller.click(selector))
    
    def fill(self, selector: str, text: str):
        return self._run(self._async_controller.fill(selector, text))
    
    def screenshot(self, full_page: bool = False):
        return self._run(self._async_controller.screenshot(full_page))
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()
