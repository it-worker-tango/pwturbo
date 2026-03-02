"""
文件下载测试

测试覆盖：
- 登录后点击按钮触发文件下载
- 等待下载完成并验证文件
- 自定义下载路径
- JSON 文件下载
- 后台异步下载不阻塞主流程

运行前请确保测试网站已启动：
    cd test_site && uv run python manage.py runserver
"""
import asyncio
import os
import pytest
from pwturbo import WebDriver, FileDownloader

BASE_URL = "http://localhost:8000"


async def _login(driver: WebDriver):
    """辅助函数：登录并返回 page"""
    page = await driver.new_page()
    await page.goto(f"{BASE_URL}/accounts/login/")
    await page.element("#username").fill("admin")
    await page.element("#password").fill("admin123")
    await page.element("button[type='submit']").click()
    await asyncio.sleep(1)
    return page


@pytest.mark.asyncio
async def test_下载CSV文件():
    """测试点击下载按钮触发 CSV 文件下载"""
    async with WebDriver(headless=True) as driver:
        page = await _login(driver)

        downloader = FileDownloader(download_dir="downloads/test")

        async with downloader.expect_download(page._page) as task_future:
            await page.element("#download-csv").click()

        task = await task_future
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed", f"下载失败: {task.error}"
        assert os.path.exists(task.save_path)
        assert task.file_size > 0
        print(f"✅ CSV 下载成功: {task.save_path} ({FileDownloader._format_size(task.file_size)})")


@pytest.mark.asyncio
async def test_下载到自定义路径():
    """测试将文件下载到指定路径"""
    async with WebDriver(headless=True) as driver:
        page = await _login(driver)

        custom_path = "downloads/custom/my_export.csv"
        downloader = FileDownloader(download_dir="downloads")

        async with downloader.expect_download(page._page, custom_path=custom_path) as task_future:
            await page.element("#download-csv").click()

        task = await task_future
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed"
        assert os.path.exists(custom_path)
        print(f"✅ 自定义路径下载成功: {custom_path}")


@pytest.mark.asyncio
async def test_下载JSON文件():
    """测试 JSON 文件下载"""
    async with WebDriver(headless=True) as driver:
        page = await _login(driver)

        downloader = FileDownloader(download_dir="downloads/test")

        async with downloader.expect_download(page._page) as task_future:
            await page.element("#download-json").click()

        task = await task_future
        task = await downloader.wait_for(task.task_id)

        assert task.status.value == "completed"
        assert task.save_path.endswith(".json")
        print(f"✅ JSON 下载成功: {task.save_path}")


@pytest.mark.asyncio
async def test_后台异步下载不阻塞():
    """测试后台下载不阻塞主流程"""
    async with WebDriver(headless=True) as driver:
        page = await _login(driver)
        await page.goto(f"{BASE_URL}/dashboard/")

        downloader = FileDownloader(download_dir="downloads/background")

        # 后台启动下载
        task_id = await downloader.start_background_download(
            page._page,
            "#download-csv",
            sub_dir="reports"
        )

        # 下载在后台进行，主流程继续
        await page.sync_cookies()
        response = page.request_get(f"{BASE_URL}/api/user/")
        assert response.status_code == 200
        print(f"  后台下载进行中，同时完成 API 请求: {response.json()['data']['username']}")

        # 等待下载完成
        task = await downloader.wait_for(task_id)
        assert task.status.value == "completed"
        print(f"✅ 后台异步下载完成: {task.save_path} 耗时={task.duration}s")
