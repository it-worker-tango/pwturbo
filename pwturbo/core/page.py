"""页面操作模块 - 封装页面导航、元素操作和 HTTP 请求"""
import asyncio
from typing import Optional, Dict, Any, Callable
from playwright.async_api import Page as PlaywrightPage, BrowserContext
from loguru import logger
import requests

from pwturbo.elements.element import Element


class Page:
    """
    页面封装类，提供页面导航、元素操作、截图和 requests 请求功能。

    使用示例：
        page = Page(context)
        await page.create()
        await page.goto("https://example.com")
        await page.element("#username").fill("admin")
        await page.sync_cookies()
        response = page.request_get("https://example.com/api/user/")
    """

    def __init__(self, context: BrowserContext):
        """
        初始化页面。

        参数：
            context: Playwright BrowserContext 实例
        """
        self._context = context
        self._page: Optional[PlaywrightPage] = None
        self._cookies: Dict[str, Any] = {}

    async def create(self) -> 'Page':
        """创建新标签页"""
        self._page = await self._context.new_page()
        logger.info("新标签页已创建")
        return self

    async def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 30000):
        """
        导航到指定 URL。

        参数：
            url: 目标地址
            wait_until: 等待条件，可选 load / domcontentloaded / networkidle
            timeout: 超时时间（毫秒），默认 30 秒
        """
        if not self._page:
            await self.create()
        await self._page.goto(url, wait_until=wait_until, timeout=timeout)
        logger.info(f"已导航到: {url}")

    async def close(self):
        """关闭当前标签页"""
        if self._page:
            await self._page.close()
            self._page = None
            logger.info("标签页已关闭")

    def element(self, selector: str, selector_type: str = "css") -> Element:
        """
        获取页面元素（返回 Element 封装对象，不直接使用 Playwright 原生 API）。

        参数：
            selector: 选择器字符串
            selector_type: 选择器类型
                - css: CSS 选择器（默认），如 "#username", ".btn"
                - xpath: XPath，如 "//input[@id='username']"
                - text: 文本内容，如 "登录"
                - role: ARIA 角色，如 "button"
                - placeholder: 占位符文本
                - label: 标签文本

        返回：
            Element 封装对象
        """
        return Element(self._page, selector, selector_type)

    async def sync_cookies(self):
        """
        将浏览器 cookies 同步到内部 requests session，
        同步后可通过 request_get / request_post 携带登录态发起请求。
        """
        if not self._page:
            return
        cookies = await self._context.cookies()
        self._cookies = {c['name']: c['value'] for c in cookies}
        logger.info(f"已同步 {len(self._cookies)} 个 cookies")

    def _build_session(self) -> requests.Session:
        """构建携带浏览器 cookies 的 requests session"""
        session = requests.Session()
        for name, value in self._cookies.items():
            session.cookies.set(name, value)
        return session

    def request_get(self, url: str, params: dict = None, headers: dict = None, **kwargs) -> requests.Response:
        """
        使用浏览器 cookies 发起 GET 请求（需先调用 sync_cookies）。

        参数：
            url: 请求地址
            params: URL 查询参数
            headers: 自定义请求头
            **kwargs: 其他 requests 参数

        返回：
            requests.Response 对象
        """
        session = self._build_session()
        response = session.get(url, params=params, headers=headers, **kwargs)
        logger.info(f"GET {url} → 状态码: {response.status_code}")
        return response

    def request_post(self, url: str, data: dict = None, json: dict = None, headers: dict = None, **kwargs) -> requests.Response:
        """
        使用浏览器 cookies 发起 POST 请求（需先调用 sync_cookies）。

        参数：
            url: 请求地址
            data: 表单数据
            json: JSON 数据
            headers: 自定义请求头
            **kwargs: 其他 requests 参数

        返回：
            requests.Response 对象
        """
        session = self._build_session()
        response = session.post(url, data=data, json=json, headers=headers, **kwargs)
        logger.info(f"POST {url} → 状态码: {response.status_code}")
        return response

    async def wait_for_url(self, url_pattern: str, timeout: int = 10000):
        """
        等待页面 URL 变化到指定模式。

        参数：
            url_pattern: URL 包含的字符串或正则
            timeout: 超时时间（毫秒）
        """
        if self._page:
            await self._page.wait_for_url(f"**{url_pattern}**", timeout=timeout)
            logger.debug(f"URL 已变化，包含: {url_pattern}")

    async def wait_for_selector(self, selector: str, state: str = "visible", timeout: int = 10000):
        """
        等待指定选择器出现。

        参数：
            selector: CSS 选择器
            state: 等待状态，visible / hidden / attached / detached
            timeout: 超时时间（毫秒）
        """
        if self._page:
            await self._page.wait_for_selector(selector, state=state, timeout=timeout)

    async def screenshot(self, path: str = None, full_page: bool = False) -> str:
        """
        截取当前页面截图。

        参数：
            path: 保存路径，不传则自动生成时间戳文件名
            full_page: 是否截取整页（包含滚动区域）

        返回：
            截图文件路径
        """
        if not self._page:
            return ""

        if not path:
            import time
            path = f"screenshots/{int(time.time())}.png"

        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        await self._page.screenshot(path=path, full_page=full_page)
        logger.info(f"截图已保存: {path}")
        return path

    async def execute_script(self, script: str, *args) -> Any:
        """
        在页面中执行 JavaScript 代码。

        参数：
            script: JS 代码字符串
            *args: 传递给 JS 的参数

        返回：
            JS 执行结果
        """
        if self._page:
            result = await self._page.evaluate(script, *args)
            logger.debug(f"JS 执行完成: {script[:50]}...")
            return result

    async def scroll_to_bottom(self):
        """滚动到页面底部"""
        await self.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    async def scroll_to_top(self):
        """滚动到页面顶部"""
        await self.execute_script("window.scrollTo(0, 0)")

    @property
    def url(self) -> str:
        """获取当前页面 URL"""
        return self._page.url if self._page else ""

    @property
    def cookies(self) -> Dict[str, Any]:
        """获取已同步的 cookies 字典"""
        return self._cookies.copy()

    async def __aenter__(self):
        """支持 async with 语法"""
        await self.create()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出 async with 时自动关闭标签页"""
        await self.close()
