"""浏览器管理模块 - 负责浏览器实例的创建、管理和模式切换"""
import asyncio
from typing import Optional, Dict
from playwright.async_api import async_playwright, Browser as PlaywrightBrowser, BrowserContext
from loguru import logger


class Browser:
    """
    浏览器封装类，支持多线程并发和有头/无头模式动态切换。

    使用示例：
        browser = Browser(headless=True)
        await browser.start()
        context = await browser.new_context()
        ...
        await browser.close()
    """

    def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        slow_mo: int = 0,
        **kwargs
    ):
        """
        初始化浏览器配置。

        参数：
            browser_type: 浏览器类型，支持 chromium / firefox / webkit
            headless: 是否无头模式，True=无头，False=有头（可见）
            slow_mo: 操作延迟毫秒数，调试时可设置为 500~1000 方便观察
            **kwargs: 其他传递给 playwright launch 的参数
        """
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        self.kwargs = kwargs
        self._playwright = None
        self._browser: Optional[PlaywrightBrowser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._lock = asyncio.Lock()

    async def start(self):
        """启动浏览器实例"""
        async with self._lock:
            if self._browser:
                logger.warning("浏览器已在运行中，跳过重复启动")
                return

            self._playwright = await async_playwright().start()
            launcher = getattr(self._playwright, self.browser_type)
            self._browser = await launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                **self.kwargs
            )
            mode = "无头" if self.headless else "有头"
            logger.info(f"浏览器已启动 [{self.browser_type}] 模式={mode} slow_mo={self.slow_mo}ms")

    async def close(self):
        """关闭浏览器并释放所有资源"""
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._contexts.clear()
            logger.info("浏览器已关闭，资源已释放")

    async def new_context(
        self,
        context_id: str = "default",
        viewport: dict = None,
        user_agent: str = None,
        **kwargs
    ) -> BrowserContext:
        """
        创建新的浏览器上下文（相当于独立的浏览器标签组）。

        参数：
            context_id: 上下文唯一标识，用于多线程场景区分不同会话
            viewport: 视口大小，例如 {"width": 1920, "height": 1080}
            user_agent: 自定义 User-Agent 字符串
            **kwargs: 其他 Playwright context 参数

        返回：
            BrowserContext 实例
        """
        if not self._browser:
            await self.start()

        # 如果已存在同名 context，直接复用
        if context_id in self._contexts:
            logger.debug(f"复用已有上下文: {context_id}")
            return self._contexts[context_id]

        options = {}
        if viewport:
            options["viewport"] = viewport
        if user_agent:
            options["user_agent"] = user_agent
        options.update(kwargs)

        context = await self._browser.new_context(**options)
        self._contexts[context_id] = context
        logger.info(f"新上下文已创建: [{context_id}]")
        return context

    async def get_context(self, context_id: str = "default") -> Optional[BrowserContext]:
        """获取已存在的上下文，不存在则返回 None"""
        return self._contexts.get(context_id)

    async def close_context(self, context_id: str = "default"):
        """关闭并销毁指定上下文"""
        if context_id in self._contexts:
            await self._contexts[context_id].close()
            del self._contexts[context_id]
            logger.info(f"上下文已关闭: [{context_id}]")

    async def switch_mode(self, headless: bool):
        """
        动态切换有头/无头模式（需要重启浏览器，会自动保存并恢复所有上下文的 cookies）。

        参数：
            headless: True=切换到无头，False=切换到有头（可见）
        """
        if self.headless == headless:
            mode = "无头" if headless else "有头"
            logger.info(f"当前已是{mode}模式，无需切换")
            return

        target_mode = "无头" if headless else "有头"
        logger.info(f"正在切换到{target_mode}模式...")

        # 保存所有上下文的 storage state（包含 cookies 和 localStorage）
        saved_states = {}
        for ctx_id, ctx in self._contexts.items():
            saved_states[ctx_id] = await ctx.storage_state()
            logger.debug(f"已保存上下文状态: {ctx_id}")

        # 重启浏览器
        self.headless = headless
        await self.close()
        await self.start()

        # 恢复所有上下文
        for ctx_id, state in saved_states.items():
            await self.new_context(ctx_id, storage_state=state)
            logger.debug(f"已恢复上下文: {ctx_id}")

        logger.info(f"模式切换完成 → {target_mode}")

    @property
    def is_running(self) -> bool:
        """检查浏览器是否正在运行"""
        return self._browser is not None

    @property
    def context_count(self) -> int:
        """当前活跃的上下文数量"""
        return len(self._contexts)

    async def __aenter__(self):
        """支持 async with 语法"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出 async with 时自动关闭浏览器"""
        await self.close()
