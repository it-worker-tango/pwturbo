"""有头模式测试 - 运行时你应该能看到浏览器窗口弹出"""
import asyncio
import pytest
from framework import WebDriver, sleep

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_有头模式登录可见():
    """
    有头模式完整登录流程 - 你应该看到：
    1. 浏览器窗口打开
    2. 自动填写用户名和密码
    3. 点击登录按钮
    4. 跳转到 dashboard 页面
    5. 窗口关闭
    """
    async with WebDriver(headless=False, slow_mo=300) as driver:
        page = await driver.new_page()

        print("\n=== 有头模式测试开始，请观察浏览器窗口 ===")

        await page.goto(f"{BASE_URL}/accounts/login/")
        await sleep(1, "停留观察登录页")

        await page.element("#username").fill("admin")
        await sleep(0.3, "填写用户名")

        await page.element("#password").fill("admin123")
        await sleep(0.3, "填写密码")

        await page.element("button[type='submit']").click()
        await sleep(2, "等待跳转并观察 dashboard")

        assert "dashboard" in page.url

        # 同步 cookies 并调用 API
        await page.sync_cookies()
        response = page.request_get(f"{BASE_URL}/api/user/")
        assert response.status_code == 200
        print(f"API 响应: {response.json()['data']}")

        print("=== 有头模式测试完成 ===\n")


@pytest.mark.asyncio
async def test_无头切换有头可见():
    """
    从无头切换到有头模式 - 你应该看到：
    1. 无头模式静默登录（无窗口）
    2. 切换后浏览器窗口突然出现
    3. 显示 dashboard 页面
    4. 停留 3 秒后关闭
    """
    async with WebDriver(headless=True) as driver:
        # 第一阶段：无头模式登录
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)
        print(f"\n无头模式登录成功: {page.url}")

        # 切换到有头模式
        print("切换到有头模式，浏览器窗口即将出现...")
        await driver.switch_mode(headless=False)

        # 用新的有头 context 访问 dashboard
        page2 = await driver.new_page(context_id="headful_ctx")
        await page2.goto(f"{BASE_URL}/accounts/login/")
        await page2.element("#username").fill("admin")
        await page2.element("#password").fill("admin123")
        await page2.element("button[type='submit']").click()

        await sleep(3, "有头模式停留3秒，请观察浏览器窗口")
        print(f"有头模式当前页面: {page2.url}")
        print("=== 模式切换测试完成 ===\n")
