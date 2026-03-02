"""
WebDriver 统一入口模块 - 框架的核心门面类，提供最简洁的使用方式。

用户只需通过 WebDriver 即可完成所有操作，无需关心底层细节。

使用示例：
    async with WebDriver(headless=False) as driver:
        page = await driver.new_page()
        await page.goto("https://example.com")
        await page.element("#username").fill("admin")
"""
import asyncio
from typing import Optional, List
from loguru import logger

from pwturbo.core.browser import Browser
from pwturbo.core.page import Page
from pwturbo.utils.config import Config
from pwturbo.utils.logger import setup_logger


class WebDriver:
    """
    框架统一入口类（门面模式）。

    将 Browser + Page + Config + Logger 整合在一起，
    让用户用最少的代码完成自动化任务。

    使用示例（推荐 async with 方式）：
        async with WebDriver(headless=False, slow_mo=500) as driver:
            page = await driver.new_page()
            await page.goto("http://localhost:8000/login/")
            await page.element("#username").fill("admin")
            await page.element("#password").fill("admin123")
            await page.element("button[type='submit']").click()
            await page.sync_cookies()
            resp = page.request_get("http://localhost:8000/api/user/")
            print(resp.json())

    或手动管理生命周期：
        driver = WebDriver(headless=True)
        await driver.start()
        page = await driver.new_page()
        ...
        await driver.quit()
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        slow_mo: int = 0,
        config_path: str = None,
        log_level: str = "INFO",
        log_file: str = "logs/automation.log",
    ):
        """
        初始化 WebDriver。

        参数：
            headless: 是否无头模式，False 时浏览器窗口可见
            browser_type: 浏览器类型，chromium / firefox / webkit
            slow_mo: 操作延迟（毫秒），调试时设置 500~1000 方便观察
            config_path: 配置文件路径（yaml），不传则使用默认配置
            log_level: 日志级别，DEBUG / INFO / WARNING / ERROR
            log_file: 日志文件路径
        """
        # 加载配置
        self.config = Config(config_path)

        # 配置优先级：构造参数 > 配置文件 > 默认值
        self.headless = headless if headless is not None else self.config.get("browser.headless", True)
        self.browser_type = browser_type or self.config.get("browser.type", "chromium")
        self.slow_mo = slow_mo or self.config.get("browser.slow_mo", 0)

        # 初始化日志
        setup_logger(level=log_level, log_file=log_file)

        # 初始化浏览器
        self._browser = Browser(
            browser_type=self.browser_type,
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        self._pages: List[Page] = []
        self._plugins = {}

        logger.info(f"WebDriver 初始化完成 [{'无头' if self.headless else '有头'}模式]")

    async def start(self):
        """启动浏览器"""
        await self._browser.start()

    async def quit(self):
        """关闭浏览器并清理所有资源"""
        # 清理插件
        for plugin in self._plugins.values():
            await plugin.cleanup()

        await self._browser.close()
        self._pages.clear()
        logger.info("WebDriver 已退出")

    async def new_page(self, context_id: str = "default", **context_kwargs) -> Page:
        """
        创建新页面（自动创建对应的浏览器上下文）。

        参数：
            context_id: 上下文 ID，多线程场景下用于隔离不同会话
            **context_kwargs: 传递给 browser.new_context 的额外参数

        返回：
            Page 封装对象
        """
        context = await self._browser.new_context(context_id=context_id, **context_kwargs)
        page = Page(context)
        await page.create()
        self._pages.append(page)
        return page

    async def switch_mode(self, headless: bool):
        """
        动态切换有头/无头模式（运行中切换，自动保存 cookies）。

        参数：
            headless: True=无头，False=有头（可见）
        """
        await self._browser.switch_mode(headless)
        self.headless = headless

    def use_plugin(self, name: str, plugin):
        """
        注册插件（数据库、自定义日志等扩展功能）。

        参数：
            name: 插件名称（唯一标识）
            plugin: 插件实例（需继承 framework.plugins.base.Plugin）

        使用示例：
            driver.use_plugin("db", DatabasePlugin("sqlite:///test.db"))
        """
        self._plugins[name] = plugin
        logger.info(f"插件已注册: {name}")

    def get_plugin(self, name: str):
        """
        获取已注册的插件。

        参数：
            name: 插件名称

        返回：
            插件实例，不存在则返回 None
        """
        return self._plugins.get(name)

    async def run_concurrent(self, tasks: list, max_workers: int = None) -> list:
        """
        并发执行多个异步任务（多线程场景）。

        参数：
            tasks: 异步任务列表（coroutine 列表）
            max_workers: 最大并发数，None 表示不限制

        返回：
            所有任务的结果列表

        使用示例：
            async def login_task(user):
                page = await driver.new_page(context_id=user)
                await page.goto("http://localhost:8000/login/")
                ...

            results = await driver.run_concurrent([
                login_task("user1"),
                login_task("user2"),
                login_task("user3"),
            ])
        """
        if max_workers:
            # 使用信号量限制并发数
            semaphore = asyncio.Semaphore(max_workers)

            async def limited_task(task):
                async with semaphore:
                    return await task

            tasks = [limited_task(t) for t in tasks]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        success = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - success
        logger.info(f"并发任务完成: 成功={success}, 失败={failed}, 总计={len(results)}")

        return list(results)

    @property
    def browser(self) -> Browser:
        """获取底层 Browser 实例（高级用法）"""
        return self._browser

    async def __aenter__(self):
        """支持 async with 语法"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出 async with 时自动关闭"""
        await self.quit()
