"""页面基类模块 - 用户继承此类来封装自己的页面对象（Page Object 模式）"""
from loguru import logger
from framework.core.page import Page
from framework.elements.element import Element


class BasePage:
    """
    页面对象基类（Page Object Model）。

    用户通过继承此类来封装具体页面的操作，
    将页面元素定位和业务操作集中管理，提高代码复用性和可维护性。

    使用示例：
        class LoginPage(BasePage):
            # 定义页面元素
            @property
            def username_input(self):
                return self.element("#username")

            @property
            def password_input(self):
                return self.element("#password")

            @property
            def login_button(self):
                return self.element("button[type='submit']")

            # 封装业务操作
            async def login(self, username: str, password: str):
                await self.username_input.fill(username)
                await self.password_input.fill(password)
                await self.login_button.click()
                await self.page.wait_for_url("dashboard")
                self.log(f"登录成功: {username}")

        # 使用方式
        login_page = LoginPage(page)
        await login_page.login("admin", "admin123")
    """

    def __init__(self, page: Page):
        """
        初始化页面对象。

        参数：
            page: Page 封装实例
        """
        self.page = page
        self._name = self.__class__.__name__

    def element(self, selector: str, selector_type: str = "css") -> Element:
        """
        获取页面元素（代理到 Page.element）。

        参数：
            selector: 选择器字符串
            selector_type: 选择器类型（css / xpath / text / role / placeholder / label）
        """
        return self.page.element(selector, selector_type)

    async def goto(self, url: str, **kwargs):
        """导航到指定 URL"""
        await self.page.goto(url, **kwargs)

    async def screenshot(self, path: str = None) -> str:
        """截取当前页面截图"""
        return await self.page.screenshot(path)

    def log(self, message: str, level: str = "info"):
        """
        输出带页面名称前缀的日志。

        参数：
            message: 日志内容
            level: 日志级别（info / debug / warning / error）
        """
        log_func = getattr(logger, level, logger.info)
        log_func(f"[{self._name}] {message}")

    @property
    def url(self) -> str:
        """获取当前页面 URL"""
        return self.page.url
