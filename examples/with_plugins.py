"""
插件使用示例 - 展示截图插件和数据库插件的使用

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from framework import WebDriver
from framework.plugins.screenshot import ScreenshotPlugin
from framework.plugins.database import DatabasePlugin

BASE_URL = "http://localhost:8000"


async def main():
    async with WebDriver(headless=True) as driver:
        # 注册插件
        screenshot_plugin = ScreenshotPlugin("screenshots")
        db_plugin = DatabasePlugin("results/test_results.json")

        driver.use_plugin("screenshot", screenshot_plugin)
        driver.use_plugin("db", db_plugin)

        # 初始化插件
        await screenshot_plugin.initialize()
        await db_plugin.initialize()

        page = await driver.new_page()
        test_name = "test_login_with_plugins"

        try:
            await page.goto(f"{BASE_URL}/accounts/login/")

            await page.element("#username").fill("admin")
            await page.element("#password").fill("admin123")
            await page.element("button[type='submit']").click()
            await asyncio.sleep(1)

            # 截图保存成功状态
            await screenshot_plugin.capture(page, "登录成功", success=True)

            # 保存测试结果到数据库
            await db_plugin.save_result({
                "test_name": test_name,
                "status": "passed",
                "url": page.url,
            })

            print(f"测试通过，截图和结果已保存")

        except Exception as e:
            # 失败时自动截图
            await screenshot_plugin.capture_on_failure(page, test_name)
            await db_plugin.save_result({
                "test_name": test_name,
                "status": "failed",
                "error": str(e),
            })
            print(f"测试失败: {e}")

        # 查询所有结果
        all_results = await db_plugin.get_results()
        print(f"\n历史测试结果（共 {len(all_results)} 条）：")
        for r in all_results:
            print(f"  [{r['timestamp']}] {r['test_name']}: {r['status']}")


if __name__ == "__main__":
    asyncio.run(main())
