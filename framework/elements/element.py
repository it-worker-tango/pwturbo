"""元素封装模块 - 封装所有元素操作，避免直接使用 Playwright 原生 API"""
from typing import Optional, List, Any
from playwright.async_api import Page as PlaywrightPage, Locator
from loguru import logger


class Element:
    """
    页面元素封装类，提供统一的元素操作接口。

    所有操作均通过此类完成，不直接暴露 Playwright Locator，
    方便后续统一添加重试、日志、截图等增强功能。

    使用示例：
        el = page.element("#username")
        await el.fill("admin")
        await el.click()
        text = await el.get_text()
    """

    def __init__(self, page: PlaywrightPage, selector: str, selector_type: str = "css"):
        """
        初始化元素。

        参数：
            page: Playwright Page 实例
            selector: 选择器字符串
            selector_type: 选择器类型（css / xpath / text / role / placeholder / label）
        """
        self._page = page
        self._selector = selector
        self._selector_type = selector_type
        self._locator: Optional[Locator] = None

    def _get_locator(self) -> Locator:
        """根据选择器类型获取 Playwright Locator（内部方法）"""
        if self._locator:
            return self._locator

        if self._selector_type == "css":
            self._locator = self._page.locator(self._selector)
        elif self._selector_type == "xpath":
            self._locator = self._page.locator(f"xpath={self._selector}")
        elif self._selector_type == "text":
            self._locator = self._page.get_by_text(self._selector)
        elif self._selector_type == "role":
            self._locator = self._page.get_by_role(self._selector)
        elif self._selector_type == "placeholder":
            self._locator = self._page.get_by_placeholder(self._selector)
        elif self._selector_type == "label":
            self._locator = self._page.get_by_label(self._selector)
        else:
            self._locator = self._page.locator(self._selector)

        return self._locator

    # ==================== 交互操作 ====================

    async def click(self, force: bool = False, timeout: int = 5000, **kwargs):
        """
        点击元素。

        参数：
            force: 是否强制点击（跳过可见性检查）
            timeout: 超时时间（毫秒）
        """
        await self._get_locator().click(force=force, timeout=timeout, **kwargs)
        logger.debug(f"点击元素: [{self._selector_type}] {self._selector}")

    async def double_click(self, **kwargs):
        """双击元素"""
        await self._get_locator().dblclick(**kwargs)
        logger.debug(f"双击元素: {self._selector}")

    async def right_click(self, **kwargs):
        """右键点击元素"""
        await self._get_locator().click(button="right", **kwargs)
        logger.debug(f"右键点击: {self._selector}")

    async def fill(self, value: str, timeout: int = 5000, **kwargs):
        """
        清空并填写输入框。

        参数：
            value: 要填写的文本
            timeout: 超时时间（毫秒）
        """
        await self._get_locator().fill(value, timeout=timeout, **kwargs)
        logger.debug(f"填写元素: [{self._selector}] 内容='{value}'")

    async def type(self, text: str, delay: int = 80):
        """
        模拟真人逐字输入（带延迟）。

        参数：
            text: 要输入的文本
            delay: 每个字符之间的延迟（毫秒），模拟真人输入速度
        """
        await self._get_locator().type(text, delay=delay)
        logger.debug(f"模拟输入: [{self._selector}] 内容='{text}'")

    async def clear(self):
        """清空输入框内容"""
        await self._get_locator().clear()
        logger.debug(f"已清空: {self._selector}")

    async def press(self, key: str):
        """
        按下键盘按键。

        参数：
            key: 按键名称，如 "Enter", "Tab", "Escape", "ArrowDown"
        """
        await self._get_locator().press(key)
        logger.debug(f"按键: [{self._selector}] key={key}")

    async def select_option(self, value: str = None, label: str = None, index: int = None):
        """
        选择下拉框选项。

        参数：
            value: 按 value 属性选择
            label: 按显示文本选择
            index: 按索引选择（从 0 开始）
        """
        locator = self._get_locator()
        if value:
            await locator.select_option(value=value)
        elif label:
            await locator.select_option(label=label)
        elif index is not None:
            await locator.select_option(index=index)
        logger.debug(f"选择下拉选项: [{self._selector}]")

    async def check(self):
        """勾选复选框"""
        await self._get_locator().check()
        logger.debug(f"已勾选: {self._selector}")

    async def uncheck(self):
        """取消勾选复选框"""
        await self._get_locator().uncheck()
        logger.debug(f"已取消勾选: {self._selector}")

    async def hover(self):
        """鼠标悬停到元素上"""
        await self._get_locator().hover()
        logger.debug(f"鼠标悬停: {self._selector}")

    async def focus(self):
        """聚焦元素"""
        await self._get_locator().focus()
        logger.debug(f"已聚焦: {self._selector}")

    async def scroll_into_view(self):
        """滚动页面使元素进入可视区域"""
        await self._get_locator().scroll_into_view_if_needed()
        logger.debug(f"已滚动到元素: {self._selector}")

    async def upload_file(self, file_path: str):
        """
        上传文件（用于 input[type=file] 元素）。

        参数：
            file_path: 本地文件路径
        """
        await self._get_locator().set_input_files(file_path)
        logger.debug(f"已上传文件: {file_path}")

    # ==================== 状态获取 ====================

    async def get_text(self) -> str:
        """获取元素的文本内容"""
        text = await self._get_locator().text_content()
        return (text or "").strip()

    async def get_inner_text(self) -> str:
        """获取元素的 innerText（不含 HTML 标签）"""
        return await self._get_locator().inner_text()

    async def get_inner_html(self) -> str:
        """获取元素的 innerHTML"""
        return await self._get_locator().inner_html()

    async def get_value(self) -> str:
        """获取输入框的当前值"""
        return await self._get_locator().input_value()

    async def get_attribute(self, name: str) -> Optional[str]:
        """
        获取元素属性值。

        参数：
            name: 属性名，如 "href", "class", "data-id"
        """
        return await self._get_locator().get_attribute(name)

    async def get_all_text(self) -> List[str]:
        """获取所有匹配元素的文本列表（用于列表场景）"""
        return await self._get_locator().all_text_contents()

    async def is_visible(self) -> bool:
        """判断元素是否可见"""
        return await self._get_locator().is_visible()

    async def is_hidden(self) -> bool:
        """判断元素是否隐藏"""
        return await self._get_locator().is_hidden()

    async def is_enabled(self) -> bool:
        """判断元素是否可交互（未禁用）"""
        return await self._get_locator().is_enabled()

    async def is_disabled(self) -> bool:
        """判断元素是否被禁用"""
        return await self._get_locator().is_disabled()

    async def is_checked(self) -> bool:
        """判断复选框是否已勾选"""
        return await self._get_locator().is_checked()

    async def count(self) -> int:
        """获取匹配该选择器的元素数量"""
        return await self._get_locator().count()

    # ==================== 等待操作 ====================

    async def wait_for(self, state: str = "visible", timeout: int = 10000):
        """
        等待元素达到指定状态。

        参数：
            state: 目标状态
                - visible: 可见（默认）
                - hidden: 隐藏
                - attached: 已挂载到 DOM
                - detached: 已从 DOM 移除
            timeout: 超时时间（毫秒）
        """
        await self._get_locator().wait_for(state=state, timeout=timeout)
        logger.debug(f"等待元素 [{self._selector}] 状态={state} 完成")

    async def wait_for_visible(self, timeout: int = 10000):
        """等待元素可见"""
        await self.wait_for("visible", timeout)

    async def wait_for_hidden(self, timeout: int = 10000):
        """等待元素隐藏"""
        await self.wait_for("hidden", timeout)

    # ==================== 截图 ====================

    async def screenshot(self, path: str = None) -> str:
        """
        对单个元素截图。

        参数：
            path: 保存路径，不传则自动生成时间戳文件名

        返回：
            截图文件路径
        """
        if not path:
            import time
            path = f"screenshots/element_{int(time.time())}.png"

        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        await self._get_locator().screenshot(path=path)
        logger.debug(f"元素截图已保存: {path}")
        return path

    # ==================== 集合操作 ====================

    def nth(self, index: int) -> 'Element':
        """
        获取第 N 个匹配的元素（从 0 开始）。

        参数：
            index: 索引，0 表示第一个
        """
        new_el = Element(self._page, self._selector, self._selector_type)
        new_el._locator = self._get_locator().nth(index)
        return new_el

    def first(self) -> 'Element':
        """获取第一个匹配的元素"""
        return self.nth(0)

    def last(self) -> 'Element':
        """获取最后一个匹配的元素"""
        new_el = Element(self._page, self._selector, self._selector_type)
        new_el._locator = self._get_locator().last()
        return new_el

    def filter(self, has_text: str = None) -> 'Element':
        """
        按条件过滤元素。

        参数：
            has_text: 过滤包含指定文本的元素
        """
        new_el = Element(self._page, self._selector, self._selector_type)
        if has_text:
            new_el._locator = self._get_locator().filter(has_text=has_text)
        return new_el

    def __repr__(self):
        return f"Element([{self._selector_type}] {self._selector})"
