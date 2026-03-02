"""
Page Object 模式示例 - 展示如何用 BasePage 封装页面操作

Page Object 模式是自动化测试的最佳实践：
- 将页面元素定位集中管理
- 将业务操作封装为方法
- 测试代码只调用业务方法，不关心元素定位细节

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from pwturbo import WebDriver, BasePage

BASE_URL = "http://localhost:8000"


class LoginPage(BasePage):
    """登录页面对象"""

    # 页面元素定义（集中管理，修改时只需改这里）
    @property
    def username_input(self):
        return self.element("#username")

    @property
    def password_input(self):
        return self.element("#password")

    @property
    def submit_button(self):
        return self.element("button[type='submit']")

    @property
    def error_message(self):
        return self.element(".error")

    # 业务操作封装
    async def open(self):
        """打开登录页"""
        await self.goto(f"{BASE_URL}/accounts/login/")
        self.log("登录页已打开")

    async def login(self, username: str, password: str):
        """执行登录操作"""
        await self.username_input.fill(username)
        await self.password_input.fill(password)
        await self.submit_button.click()
        await asyncio.sleep(1)
        self.log(f"已提交登录: {username}")

    async def get_error(self) -> str:
        """获取错误提示信息"""
        if await self.error_message.is_visible():
            return await self.error_message.get_text()
        return ""


class DashboardPage(BasePage):
    """控制台页面对象"""

    @property
    def welcome_text(self):
        return self.element("h1")

    @property
    def logout_button(self):
        return self.element(".logout-btn")

    async def get_welcome_message(self) -> str:
        """获取欢迎信息"""
        return await self.welcome_text.get_text()

    async def logout(self):
        """退出登录"""
        await self.logout_button.click()
        self.log("已退出登录")


async def main():
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        # 使用页面对象，测试代码清晰易读
        login_page = LoginPage(page)
        await login_page.open()

        # 测试错误登录
        await login_page.login("wrong_user", "wrong_pass")
        error = await login_page.get_error()
        print(f"错误提示: {error}")

        # 测试正确登录
        await login_page.open()
        await login_page.login("admin", "admin123")

        # 验证跳转到 dashboard
        dashboard = DashboardPage(page)
        welcome = await dashboard.get_welcome_message()
        print(f"欢迎信息: {welcome}")

        # 截图
        await page.screenshot("screenshots/dashboard.png")
        print("截图已保存")


if __name__ == "__main__":
    asyncio.run(main())
