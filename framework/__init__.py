"""
pwturbo - 基于 Playwright 的多线程 Web 自动化框架

快速开始：
    from framework import WebDriver

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
from framework.core.driver import WebDriver
from framework.core.browser import Browser
from framework.core.page import Page
from framework.core.base_page import BasePage
from framework.core.downloader import FileDownloader, DownloadTask, DownloadStatus
from framework.elements.element import Element
from framework.utils.wait import wait_until, retry, sleep, retry_decorator
from framework.utils.config import Config
from framework.utils.logger import setup_logger
from framework.auth.okta import OktaHandler, Win32DialogHandler

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
