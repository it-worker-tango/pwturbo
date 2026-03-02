"""框架单元测试 - 测试核心组件的基础功能（无需启动测试网站）"""
import pytest
from pwturbo.core.browser import Browser
from pwturbo.core.page import Page
from pwturbo import WebDriver


@pytest.mark.asyncio
async def test_浏览器启动与关闭():
    """测试浏览器能正常启动和关闭"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()

    assert browser.is_running

    await browser.close()
    assert not browser.is_running


@pytest.mark.asyncio
async def test_页面创建():
    """测试页面对象能正常创建"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()

    context = await browser.new_context()
    page = Page(context)
    await page.create()

    assert page._page is not None

    await browser.close()


@pytest.mark.asyncio
async def test_元素属性读取():
    """测试元素封装能正确读取属性（使用 data URI，无需外部服务）"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()

    context = await browser.new_context()
    page = Page(context)
    await page.create()

    await page.goto("data:text/html,<input id='test' value='hello'>")

    el = page.element("#test")
    value = await el.get_attribute("value")
    assert value == "hello"

    await browser.close()


@pytest.mark.asyncio
async def test_元素可见性与状态():
    """测试元素可见性、启用状态等判断方法"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(
            "data:text/html,"
            "<input id='enabled' value='test'>"
            "<input id='disabled' disabled>"
            "<div id='hidden' style='display:none'>隐藏</div>"
            "<div id='visible'>可见</div>"
        )

        assert await page.element("#enabled").is_enabled()
        assert await page.element("#disabled").is_disabled()
        assert await page.element("#hidden").is_hidden()
        assert await page.element("#visible").is_visible()


@pytest.mark.asyncio
async def test_元素填写与读值():
    """测试 fill 填写后 get_value 能正确读取"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto("data:text/html,<input id='t' type='text'>")

        await page.element("#t").fill("pwturbo")
        value = await page.element("#t").get_value()
        assert value == "pwturbo"


@pytest.mark.asyncio
async def test_元素计数():
    """测试 count() 返回匹配元素数量"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto(
            "data:text/html,"
            "<ul><li>A</li><li>B</li><li>C</li></ul>"
        )

        count = await page.element("li").count()
        assert count == 3


@pytest.mark.asyncio
async def test_元素文本获取():
    """测试 get_text 能正确获取元素文本"""
    async with WebDriver(headless=True) as driver:
        page = await driver.new_page()
        await page.goto("data:text/html,<h1 id='title'>pwturbo</h1>")

        text = await page.element("#title").get_text()
        assert text == "pwturbo"


@pytest.mark.asyncio
async def test_有头无头模式切换():
    """测试运行时动态切换有头/无头模式"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()

    assert browser.headless is True

    await browser.switch_mode(headless=False)
    assert browser.headless is False

    await browser.close()


@pytest.mark.asyncio
async def test_WebDriver上下文管理器():
    """测试 WebDriver async with 能正常启动和退出"""
    async with WebDriver(headless=True) as driver:
        assert driver._browser.is_running
        page = await driver.new_page()
        assert page is not None
        assert page.url == "about:blank"
