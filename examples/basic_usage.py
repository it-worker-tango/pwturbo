"""
基础使用示例 - 展示框架最简洁的使用方式

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from pwturbo import WebDriver


async def main():
    # 推荐使用 async with，自动管理浏览器生命周期
    async with WebDriver(headless=True) as driver:
        # 创建页面
        page = await driver.new_page()

        # 导航到登录页
        await page.goto("http://localhost:8000/accounts/login/")

        # 使用自定义元素封装填写表单（不直接使用 Playwright API）
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()

        # 等待跳转
        await asyncio.sleep(1)
        print(f"当前页面: {page.url}")

        # 同步 cookies 后用 requests 调用 API
        await page.sync_cookies()
        response = page.request_get("http://localhost:8000/api/user/")
        print(f"用户信息: {response.json()}")

        response = page.request_get("http://localhost:8000/api/data/")
        print(f"测试数据: {response.json()}")


if __name__ == "__main__":
    asyncio.run(main())
