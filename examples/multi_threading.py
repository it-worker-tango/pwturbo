"""
多线程并发示例 - 展示如何同时运行多个浏览器会话

适用场景：
- 并发测试多个用户同时登录
- 批量数据采集
- 压力测试

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
from pwturbo import WebDriver

BASE_URL = "http://localhost:8000"


async def user_session(driver: WebDriver, user_id: int):
    """单个用户会话任务"""
    context_id = f"user_{user_id}"

    # 每个用户使用独立的浏览器上下文（隔离 cookies）
    page = await driver.new_page(context_id=context_id)

    await page.goto(f"{BASE_URL}/accounts/login/")
    await page.element("#username").fill("admin")
    await page.element("#password").fill("admin123")
    await page.element("button[type='submit']").click()
    await asyncio.sleep(1)

    # 同步 cookies 并调用 API
    await page.sync_cookies()
    response = page.request_get(f"{BASE_URL}/api/user/")
    data = response.json()

    print(f"[用户 {user_id}] 登录成功，当前页面: {page.url}")
    print(f"[用户 {user_id}] API 响应: {data['data']['username']}")

    return {"user_id": user_id, "status": "success", "url": page.url}


async def main():
    async with WebDriver(headless=True) as driver:
        print("开始并发测试（3个用户同时登录）...")

        # 方式一：使用 driver.run_concurrent（推荐，支持限制并发数）
        results = await driver.run_concurrent(
            tasks=[user_session(driver, i) for i in range(1, 4)],
            max_workers=3,  # 最多同时运行 3 个
        )

        print(f"\n并发测试完成，结果：")
        for r in results:
            if isinstance(r, Exception):
                print(f"  失败: {r}")
            else:
                print(f"  用户 {r['user_id']}: {r['status']}")


if __name__ == "__main__":
    asyncio.run(main())
