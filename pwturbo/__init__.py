"""
pwturbo - 基于 Playwright 的多线程 Web 自动化框架

快速开始：
    from pwturbo import WebDriver

    async with WebDriver(headless=False) as driver:
        page = await driver.new_page()
        await page.goto("http://localhost:8000/accounts/login/")
        await page.element("#username").fill("admin")
        await page.element("#password").fill("admin123")
        await page.element("button[type='submit']").click()
        await page.sync_cookies()
        resp = page.request_get("http://localhost:8000/api/user/")
        print(resp.json())
"""
from pwturbo.core.driver import WebDriver
from pwturbo.core.browser import Browser
from pwturbo.core.page import Page
from pwturbo.core.base_page import BasePage
from pwturbo.core.downloader import FileDownloader, DownloadTask, DownloadStatus
from pwturbo.elements.element import Element
from pwturbo.utils.wait import wait_until, retry, sleep, retry_decorator
from pwturbo.utils.config import Config
from pwturbo.utils.logger import setup_logger
from pwturbo.auth.okta import OktaHandler, Win32DialogHandler

__version__ = "0.3.0"
__all__ = [
    "WebDriver",
    "Browser",
    "Page",
    "BasePage",
    "FileDownloader",
    "DownloadTask",
    "DownloadStatus",
    "Element",
    "wait_until",
    "retry",
    "sleep",
    "retry_decorator",
    "Config",
    "setup_logger",
    "OktaHandler",
    "Win32DialogHandler",
]
