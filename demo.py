"""
Web 自动化框架 - 主入口

演示框架的核心功能，运行前请先启动测试网站：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from framework import WebDriver

BASE_URL = "http://localhost:8000"


async def main():
    # 使用 async with 自动管理浏览器生命周期
    async with WebDriver(
        headless=True,          # 无头模式（改为 False 可看到浏览器窗口）
        browser_type="chromium",
        slow_mo=0,              # 调试时可设置为 500，方便观察每步操作
        log_level="INFO",
    ) as driver:

        page = await driver.new_page()

        # 打开登录页
        await page.goto(f"{BASE_URL}/accounts/login/")

        # 使用封装的元素操作（不直接使用 Playwright API）
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()

        await asyncio.sleep(1)
        print(f"登录成功，当前页面: {page.url}")

        # 同步 cookies 后通过 requests 调用 API
        await page.sync_cookies()

        user_resp = page.request_get(f"{BASE_URL}/api/user/")
        print(f"用户信息: {user_resp.json()}")

        data_resp = page.request_get(f"{BASE_URL}/api/data/")
        print(f"测试数据: {data_resp.json()}")

        # 截图
        await page.screenshot("screenshots/main_demo.png")
        print("截图已保存: screenshots/main_demo.png")


if __name__ == "__main__":
    asyncio.run(main())
