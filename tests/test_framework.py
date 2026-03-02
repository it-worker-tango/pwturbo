"""Framework unit tests"""
import pytest
import asyncio
from framework.core.browser import Browser
from framework.core.page import Page


@pytest.mark.asyncio
async def test_browser_start():
    """Test browser initialization"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()
    
    assert browser.is_running
    
    await browser.close()
    assert not browser.is_running


@pytest.mark.asyncio
async def test_page_creation():
    """Test page creation"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()
    
    context = await browser.new_context()
    page = Page(context)
    await page.create()
    
    assert page._page is not None
    
    await browser.close()


@pytest.mark.asyncio
async def test_element_operations():
    """Test element wrapper operations"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()
    
    context = await browser.new_context()
    page = Page(context)
    await page.create()
    
    # Navigate to a test page
    await page.goto("data:text/html,<input id='test' value='hello'>")
    
    element = page.element("#test")
    value = await element.get_attribute("value")
    
    assert value == "hello"
    
    await browser.close()


@pytest.mark.asyncio
async def test_mode_switching():
    """Test headless/headful mode switching"""
    browser = Browser(browser_type="chromium", headless=True)
    await browser.start()
    
    assert browser.headless == True
    
    await browser.switch_mode(headless=False)
    assert browser.headless == False
    
    await browser.close()
