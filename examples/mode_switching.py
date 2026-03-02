"""
有头/无头模式切换示例 - 展示运行中动态切换浏览器模式

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from pwturbo import WebDriver, sleep

BASE_URL = "http://localhost:8000"


async def main():
    # 从无头模式开始
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        print("第一阶段：无头模式（后台运行，无窗口）")
        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)
        print(f"  无头模式登录成功: {page.url}")

        print("\n切换到有头模式（浏览器窗口即将出现）...")
        await driver.switch_mode(headless=False)

        # 切换后需要重新创建页面（新的 context）
        page2 = await driver.new_page(context_id="headful")
        await page2.goto(f"{BASE_URL}/accounts/login/")
        await page2.element("#username").fill("admin")
        await page2.element("#password").fill("admin123")
        await page2.element("button[type='submit']").click()

        print("第二阶段：有头模式（你应该能看到浏览器窗口）")
        await sleep(3, "停留3秒，观察浏览器窗口")
        print(f"  有头模式当前页面: {page2.url}")

        print("\n切换回无头模式...")
        await driver.switch_mode(headless=True)
        print("已切换回无头模式，窗口已关闭")


if __name__ == "__main__":
    asyncio.run(main())
