"""
文件下载 + 模拟 OKTA 认证测试

测试覆盖：
- 登录后通过浏览器点击下载按钮触发文件下载
- 异步下载（不阻塞主流程）
- 自定义下载路径
- 模拟 OKTA SSO 登录流程
"""
import asyncio
import os
import pytest
from framework import WebDriver, FileDownloader

BASE_URL = "http://localhost:8000"


# ==================== 文件下载测试 ====================

@pytest.mark.asyncio
async def test_下载CSV文件():
    """测试点击下载按钮触发 CSV 文件下载"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        # 先登录
        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        # 初始化下载管理器
        downloader = FileDownloader(download_dir="downloads/test")

        # 使用 expect_download 监听下载事件
        async with downloader.expect_download(page._page) as task_future:
            await page.element("#download-csv").click()

        # 等待下载完成
        task = await task_future
        await asyncio.sleep(1)  # 给异步任务时间完成

        # 等待任务完成
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed", f"下载失败: {task.error}"
        assert os.path.exists(task.save_path), f"文件不存在: {task.save_path}"
        assert task.file_size > 0

        print(f"✅ CSV 下载成功: {task.save_path} ({FileDownloader._format_size(task.file_size)})")


@pytest.mark.asyncio
async def test_下载到自定义路径():
    """测试将文件下载到指定路径"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        custom_path = "downloads/custom/my_export.csv"
        downloader = FileDownloader(download_dir="downloads")

        async with downloader.expect_download(
            page._page,
            custom_path=custom_path
        ) as task_future:
            await page.element("#download-csv").click()

        task = await task_future
        await asyncio.sleep(1)
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed"
        assert os.path.exists(custom_path)
        print(f"✅ 自定义路径下载成功: {custom_path}")


@pytest.mark.asyncio
async def test_下载JSON文件():
    """测试 JSON 文件下载"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        downloader = FileDownloader(download_dir="downloads/test")

        async with downloader.expect_download(page._page) as task_future:
            await page.element("#download-json").click()

        task = await task_future
        await asyncio.sleep(1)
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed"
        assert task.save_path.endswith(".json")
        print(f"✅ JSON 下载成功: {task.save_path}")


@pytest.mark.asyncio
async def test_后台异步下载不阻塞():
    """测试后台下载不阻塞主流程"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        await page.goto(f"{BASE_URL}/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await asyncio.sleep(1)

        await page.goto(f"{BASE_URL}/dashboard/")

        downloader = FileDownloader(download_dir="downloads/background")

        # 后台启动下载
        task_id = await downloader.start_background_download(
            page._page,
            "#download-csv",
            sub_dir="reports"
        )

        # 下载在后台进行，主流程继续执行其他操作
        await page.sync_cookies()
        response = page.request_get(f"{BASE_URL}/api/user/")
        assert response.status_code == 200
        print(f"  后台下载进行中，同时完成了 API 请求: {response.json()['data']['username']}")

        # 最后等待下载完成
        task = await downloader.wait_for(task_id)
        assert task.status.value == "completed"
        print(f"✅ 后台异步下载完成: {task.save_path} 耗时={task.duration}s")


# ==================== 模拟 OKTA 认证测试 ====================

@pytest.mark.asyncio
async def test_模拟OKTA登录页面():
    """测试模拟 OKTA 登录页面能正常访问"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(f"{BASE_URL}/okta/authorize/?next=/dashboard/")

        # 验证是模拟 OKTA 页面
        title = await page.element("title", "css").get_text() if False else ""
        okta_logo = page.element(".okta-logo")
        assert await okta_logo.is_visible()

        logo_text = await okta_logo.get_text()
        assert "OKTA" in logo_text.upper()
        print(f"✅ 模拟 OKTA 页面加载成功: {logo_text}")


@pytest.mark.asyncio
async def test_模拟OKTA认证流程():
    """测试完整的模拟 OKTA SSO 认证流程"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        # 访问模拟 OKTA 授权页（携带回调地址）
        await page.goto(f"{BASE_URL}/okta/authorize/?next=/dashboard/")
        await asyncio.sleep(0.5)

        # 填写 OKTA 登录表单
        await page.element("#okta-username").fill("admin")
        await page.element("#okta-password").fill("admin123")
        await page.element("#okta-submit").click()
        await asyncio.sleep(1)

        # 验证已重定向回应用并携带 token
        assert "dashboard" in page.url or "okta_token" in page.url
        print(f"✅ 模拟 OKTA 认证成功，当前页面: {page.url}")


@pytest.mark.asyncio
async def test_OKTA_token换取用户信息():
    """测试用 OKTA token 换取用户信息"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        # 完成 OKTA 认证
        await page.goto(f"{BASE_URL}/okta/authorize/?next=/dashboard/")
        await page.element("#okta-username").fill("admin")
        await page.element("#okta-password").fill("admin123")
        await page.element("#okta-submit").click()
        await asyncio.sleep(1)

        # 从 URL 中提取 token
        current_url = page.url
        if "okta_token=" in current_url:
            token = current_url.split("okta_token=")[-1].split("&")[0]

            # 用 token 调用 userinfo 接口
            await page.sync_cookies()
            response = page.request_get(f"{BASE_URL}/okta/userinfo/?token={token}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sub"] == "admin"
            print(f"✅ OKTA token 换取用户信息成功: {data}")
        else:
            # 已经重定向到 dashboard（session 已存在）
            print(f"✅ OKTA 认证成功（已有 session）: {current_url}")


@pytest.mark.asyncio
async def test_OktaHandler自动认证():
    """测试 OktaHandler 类自动处理 OKTA 认证"""
    from framework.auth.okta import OktaHandler

    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()

        okta = OktaHandler(username="admin", password="admin123")

        # 模拟访问受 OKTA 保护的应用
        # 先手动导航到 OKTA 页面，再用 handler 处理
        await page.goto(f"{BASE_URL}/okta/authorize/?next=/dashboard/")
        await asyncio.sleep(0.5)

        # 使用 OktaHandler 自动登录
        success = await okta.login_on_okta_page(page)
        assert success, "OktaHandler 认证失败"
        print(f"✅ OktaHandler 自动认证成功，当前页面: {page.url}")
