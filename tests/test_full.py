"""完整集成测试 - 覆盖框架所有核心功能"""
import asyncio
import pytest
from pwturbo import WebDriver, wait_until, retry

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_登录页面加载():
    """测试登录页面能正常访问"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        title = await page.element("h2").get_text()
        assert "登录" in title
        print(f"✅ 登录页标题: {title}")


@pytest.mark.asyncio
async def test_错误凭据被拒绝():
    """测试错误的用户名密码会显示错误提示"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        await page.element("#username").fill("不存在的用户")
        await page.element("#password").fill("错误密码")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        error_el = page.element(".error")
        assert await error_el.is_visible()
        error_text = await error_el.get_text()
        print(f"✅ 错误提示: {error_text}")


@pytest.mark.asyncio
async def test_登录成功跳转():
    """测试正确凭据登录后跳转到 dashboard"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        assert "dashboard" in page.url
        print(f"✅ 登录成功，跳转到: {page.url}")


@pytest.mark.asyncio
async def test_登录后API请求():
    """测试登录后同步 cookies 并通过 requests 调用 API"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        # 同步 cookies 后发起 API 请求
        await page.sync_cookies()
        response = page.request_get(f"{BASE_URL}/api/user/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == "admin"
        print(f"✅ API 请求成功: {data['data']}")


@pytest.mark.asyncio
async def test_测试数据API():
    """测试数据接口返回正确数据"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        await page.sync_cookies()
        response = page.request_get(f"{BASE_URL}/api/data/")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["total"] == 3
        print(f"✅ 数据 API 成功，共 {data['data']['total']} 条")


@pytest.mark.asyncio
async def test_并发多会话():
    """测试多个浏览器上下文并发登录"""
    async with WebDriver(headless=True) as driver:

        async def single_login(user_id: int):
            page = await driver.new_page(context_id=f"ctx_{user_id}")
            await page.goto(f"{BASE_URL}/accounts/login/")
            await page.element("#username").fill("admin")
            await page.element("#password").fill("admin123")
            await page.element("button[type='submit']").click()
            await asyncio.sleep(1)
            assert "dashboard" in page.url
            return user_id

        results = await driver.run_concurrent(
            [single_login(i) for i in range(3)]
        )

        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)
        print(f"✅ 并发会话成功: {results}")


@pytest.mark.asyncio
async def test_有头无头模式切换():
    """测试运行时动态切换有头/无头模式"""
    async with WebDriver(headless=True) as driver:
        assert driver.headless is True

        await driver.switch_mode(headless=False)
        assert driver.headless is False

        await driver.switch_mode(headless=True)
        assert driver.headless is True

        print("✅ 模式切换正常")


@pytest.mark.asyncio
async def test_元素操作封装():
    """测试自定义元素封装的各种操作"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        # 使用 data URI 创建测试页面，无需外部依赖
        await page.goto("data:text/html,<input id='t' value='hello'><button id='b'>点击</button>")

        el = page.element("#t")
        assert await el.get_attribute("value") == "hello"
        assert await el.is_visible()
        assert await el.is_enabled()

        await el.fill("world")
        assert await el.get_value() == "world"

        count = await page.element("input").count()
        assert count == 1

        print("✅ 元素操作封装正常")


@pytest.mark.asyncio
async def test_截图功能():
    """测试页面截图功能"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/accounts/login/")

        path = await page.screenshot("screenshots/test_login.png")
        assert path == "screenshots/test_login.png"

        import os
        assert os.path.exists(path)
        print(f"✅ 截图已保存: {path}")
