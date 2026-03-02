"""
OKTA SSO 认证模拟模块

真实 OKTA 流程：
  用户访问应用 → 重定向到 OKTA 登录页 → 输入企业账号密码
  → OKTA 验证 → 携带 token 重定向回应用 → 应用验证 token → 登录成功

本模块提供两种能力：
1. OktaHandler  - 自动化处理真实 OKTA 登录页面（填写账号密码）
2. Win32DialogHandler - 处理 Windows 系统级弹窗（NTLM/Kerberos 认证对话框）
"""
import asyncio
from typing import Optional
from loguru import logger

from framework.core.page import Page
from framework.elements.element import Element


class OktaHandler:
    """
    OKTA 登录页面自动化处理器。

    支持标准 OKTA 登录流程，包括：
    - 用户名/密码登录
    - 等待 MFA 验证码输入（如需要）
    - 自动检测并处理 OKTA 重定向

    使用示例：
        okta = OktaHandler(username="user@company.com", password="pass123")

        # 访问受 OKTA 保护的应用，自动处理认证
        await okta.authenticate(page, app_url="https://app.company.com")
    """

    # 常见 OKTA 登录页面的元素选择器（同时兼容真实 OKTA 和模拟 OKTA）
    SELECTORS = {
        # 真实 OKTA 选择器
        "username":        "#okta-signin-username",
        "password":        "#okta-signin-password",
        "submit":          "#okta-signin-submit",
        "next_button":     '[data-type="save"]',
        # 模拟 OKTA 选择器（fallback）
        "username_mock":   "#okta-username",
        "password_mock":   "#okta-password",
        "submit_mock":     "#okta-submit",
        # 通用
        "mfa_code":        'input[name="answer"]',
        "mfa_verify":      'input[value="Verify"]',
        "error_message":   ".o-form-error-container",
        "error_mock":      "#okta-error",
    }

    def __init__(
        self,
        username: str,
        password: str,
        mfa_secret: str = None,
        timeout: int = 30000,
    ):
        """
        初始化 OKTA 处理器。

        参数：
            username: OKTA 账号（通常是企业邮箱）
            password: OKTA 密码
            mfa_secret: TOTP 密钥（如果启用了 MFA，用于自动生成验证码）
            timeout: 等待超时时间（毫秒）
        """
        self.username = username
        self.password = password
        self.mfa_secret = mfa_secret
        self.timeout = timeout

    async def authenticate(self, page: Page, app_url: str) -> bool:
        """
        访问受 OKTA 保护的应用并自动完成认证。

        流程：
        1. 访问应用 URL
        2. 检测是否被重定向到 OKTA 登录页
        3. 自动填写账号密码
        4. 处理 MFA（如果需要）
        5. 等待重定向回应用

        参数：
            page: Page 封装实例
            app_url: 目标应用 URL

        返回：
            True=认证成功，False=认证失败
        """
        logger.info(f"开始 OKTA 认证流程，目标: {app_url}")
        await page.goto(app_url)
        await asyncio.sleep(2)

        # 检测是否跳转到了 OKTA 登录页
        if not self._is_okta_page(page.url):
            logger.info("未检测到 OKTA 重定向，可能已登录或不需要 OKTA 认证")
            return True

        logger.info(f"检测到 OKTA 登录页: {page.url}")
        return await self._do_login(page)

    async def login_on_okta_page(self, page: Page) -> bool:
        """
        在已经打开的 OKTA 登录页上执行登录。

        适用于已经导航到 OKTA 页面的场景。

        参数：
            page: 当前在 OKTA 登录页的 Page 实例

        返回：
            True=登录成功，False=登录失败
        """
        return await self._do_login(page)

    async def _do_login(self, page: Page) -> bool:
        """执行 OKTA 登录操作（自动检测真实 OKTA 或模拟 OKTA）"""
        try:
            # 自动检测是真实 OKTA 还是模拟 OKTA 页面
            real_username = page.element(self.SELECTORS["username"])
            mock_username = page.element(self.SELECTORS["username_mock"])

            # 等待任意一个用户名输入框出现
            is_mock = False
            for _ in range(60):  # 最多等 6 秒
                if await real_username.is_visible():
                    break
                if await mock_username.is_visible():
                    is_mock = True
                    break
                await asyncio.sleep(0.1)
            else:
                raise TimeoutError("未找到 OKTA 登录表单")

            # 根据页面类型选择选择器
            username_sel = self.SELECTORS["username_mock"] if is_mock else self.SELECTORS["username"]
            password_sel = self.SELECTORS["password_mock"] if is_mock else self.SELECTORS["password"]
            submit_sel   = self.SELECTORS["submit_mock"]   if is_mock else self.SELECTORS["submit"]
            error_sel    = self.SELECTORS["error_mock"]    if is_mock else self.SELECTORS["error_message"]

            mode = "模拟 OKTA" if is_mock else "真实 OKTA"
            logger.info(f"检测到 {mode} 登录页面")

            username_el = page.element(username_sel)
            password_el = page.element(password_sel)

            await username_el.fill(self.username)
            logger.debug(f"已填写用户名: {self.username}")

            # 检查是否有 Next 按钮（真实 OKTA 分步骤登录）
            if not is_mock:
                next_btn = page.element(self.SELECTORS["next_button"])
                if await next_btn.is_visible():
                    await next_btn.click()
                    await asyncio.sleep(1)
                    logger.debug("点击 Next 按钮（分步骤登录）")

            await password_el.fill(self.password)
            logger.debug("已填写密码")

            await page.element(submit_sel).click()
            await asyncio.sleep(2)

            # 检查是否需要 MFA（仅真实 OKTA）
            if not is_mock:
                mfa_input = page.element(self.SELECTORS["mfa_code"])
                if await mfa_input.is_visible():
                    logger.info("检测到 MFA 验证，尝试自动填写...")
                    await self._handle_mfa(page)

            # 等待重定向离开 OKTA 页面
            await self._wait_for_redirect(page)

            # 检查是否有错误
            error_el = page.element(error_sel)
            if await error_el.is_visible():
                error_text = await error_el.get_text()
                logger.error(f"OKTA 登录失败: {error_text}")
                return False

            logger.info(f"OKTA 认证成功，当前页面: {page.url}")
            return True

        except Exception as e:
            logger.error(f"OKTA 认证过程出错: {e}")
            return False

    async def _handle_mfa(self, page: Page):
        """处理 MFA 验证"""
        if self.mfa_secret:
            # 自动生成 TOTP 验证码
            code = self._generate_totp(self.mfa_secret)
            await page.element(self.SELECTORS["mfa_code"]).fill(code)
            await page.element(self.SELECTORS["mfa_verify"]).click()
            logger.info(f"已自动填写 MFA 验证码: {code}")
        else:
            logger.warning("需要 MFA 验证码，但未配置 mfa_secret，请手动输入...")
            # 等待用户手动输入（最多等 60 秒）
            await asyncio.sleep(60)

    async def _wait_for_redirect(self, page: Page, timeout: float = 30.0):
        """等待从 OKTA 页面重定向回应用"""
        start = asyncio.get_event_loop().time()
        while self._is_okta_page(page.url):
            if asyncio.get_event_loop().time() - start > timeout:
                raise TimeoutError("等待 OKTA 重定向超时")
            await asyncio.sleep(0.5)

    @staticmethod
    def _is_okta_page(url: str) -> bool:
        """判断当前 URL 是否是 OKTA 登录页（兼容真实 OKTA 和模拟 OKTA）"""
        okta_patterns = [
            "okta.com",
            "/login/login.htm",
            "sso/saml",
            "/oauth2/",
            "/okta/authorize",   # 模拟 OKTA 授权页
            "/okta/callback",    # 模拟 OKTA 回调页
        ]
        return any(p in url for p in okta_patterns)

    @staticmethod
    def _generate_totp(secret: str) -> str:
        """生成 TOTP 验证码（需要安装 pyotp）"""
        try:
            import pyotp
            totp = pyotp.TOTP(secret)
            return totp.now()
        except ImportError:
            logger.error("生成 TOTP 需要安装 pyotp: uv add pyotp")
            return ""


class Win32DialogHandler:
    """
    Windows 系统级弹窗处理器（使用 pywin32）。

    适用场景：
    - Windows 身份验证弹窗（NTLM/Kerberos）
    - 某些企业内网应用的系统级认证对话框
    - 文件下载/保存的系统对话框

    注意：此功能仅在 Windows 系统上可用，需要安装 pywin32。
    安装：uv add pywin32

    使用示例：
        handler = Win32DialogHandler()

        # 在触发弹窗的操作前注册处理器
        async with handler.handle_auth_dialog(username="domain\\user", password="pass"):
            await page.goto("https://internal-app.company.com")
    """

    def __init__(self):
        self._check_platform()

    @staticmethod
    def _check_platform():
        """检查是否在 Windows 平台"""
        import platform
        if platform.system() != "Windows":
            logger.warning("Win32DialogHandler 仅支持 Windows 系统")

    def handle_auth_dialog(self, username: str, password: str, timeout: float = 10.0):
        """
        返回异步上下文管理器，在 with 块内自动处理 Windows 身份验证弹窗。

        参数：
            username: Windows 用户名（格式：domain\\username 或 username）
            password: Windows 密码
            timeout: 等待弹窗出现的超时时间（秒）

        使用示例：
            async with handler.handle_auth_dialog("DOMAIN\\user", "password"):
                await page.goto("https://internal-site.company.com")
        """
        return _Win32AuthContext(username, password, timeout)

    async def fill_auth_dialog(self, username: str, password: str, timeout: float = 10.0) -> bool:
        """
        等待并填写 Windows 身份验证弹窗。

        参数：
            username: 用户名
            password: 密码
            timeout: 超时时间（秒）

        返回：
            True=成功处理，False=未找到弹窗或处理失败
        """
        return await _fill_windows_auth_dialog(username, password, timeout)

    async def close_dialog(self, title_keyword: str = None, timeout: float = 5.0) -> bool:
        """
        关闭指定标题的 Windows 弹窗（按 ESC 或点击取消）。

        参数：
            title_keyword: 窗口标题关键词，None 则关闭最前面的弹窗
            timeout: 超时时间（秒）

        返回：
            True=成功关闭，False=未找到弹窗
        """
        return await _close_windows_dialog(title_keyword, timeout)


async def _fill_windows_auth_dialog(username: str, password: str, timeout: float) -> bool:
    """
    使用 pywin32 填写 Windows 身份验证弹窗的具体实现。

    Windows 身份验证弹窗通常包含：
    - 用户名输入框
    - 密码输入框
    - 确定/取消按钮
    """
    try:
        import win32gui
        import win32con
        import win32api
        import time
    except ImportError:
        logger.error("处理 Windows 弹窗需要安装 pywin32: uv add pywin32")
        return False

    logger.info(f"等待 Windows 身份验证弹窗（超时 {timeout}s）...")

    # 等待弹窗出现
    start = time.time()
    dialog_hwnd = None

    # 常见的 Windows 认证弹窗标题关键词
    auth_dialog_titles = [
        "Windows 安全", "Windows Security",
        "连接到", "Connect to",
        "身份验证", "Authentication",
        "登录", "Sign in",
    ]

    while time.time() - start < timeout:
        for title in auth_dialog_titles:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:
                dialog_hwnd = hwnd
                break

        # 也尝试枚举所有顶层窗口查找认证对话框
        if not dialog_hwnd:
            def enum_callback(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    for keyword in auth_dialog_titles:
                        if keyword in title:
                            results.append(hwnd)

            found = []
            win32gui.EnumWindows(enum_callback, found)
            if found:
                dialog_hwnd = found[0]

        if dialog_hwnd:
            break

        await asyncio.sleep(0.3)

    if not dialog_hwnd:
        logger.warning("未找到 Windows 身份验证弹窗")
        return False

    dialog_title = win32gui.GetWindowText(dialog_hwnd)
    logger.info(f"找到弹窗: [{dialog_title}] hwnd={dialog_hwnd}")

    try:
        # 激活弹窗
        win32gui.SetForegroundWindow(dialog_hwnd)
        await asyncio.sleep(0.3)

        # 使用 SendKeys 填写用户名和密码
        # 先清空并填写用户名
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")

        # Tab 键切换焦点到用户名框，填写用户名
        shell.SendKeys(username)
        await asyncio.sleep(0.2)
        shell.SendKeys("{TAB}")
        await asyncio.sleep(0.2)

        # 填写密码
        shell.SendKeys(password)
        await asyncio.sleep(0.2)

        # 按 Enter 确认
        shell.SendKeys("{ENTER}")
        await asyncio.sleep(0.5)

        logger.info("Windows 身份验证弹窗已填写并提交")
        return True

    except Exception as e:
        logger.error(f"填写 Windows 弹窗失败: {e}")
        return False


async def _close_windows_dialog(title_keyword: str, timeout: float) -> bool:
    """关闭 Windows 弹窗"""
    try:
        import win32gui
        import win32con
        import time
    except ImportError:
        logger.error("需要安装 pywin32: uv add pywin32")
        return False

    start = time.time()
    while time.time() - start < timeout:
        if title_keyword:
            hwnd = win32gui.FindWindow(None, title_keyword)
        else:
            # 获取最前面的窗口
            hwnd = win32gui.GetForegroundWindow()

        if hwnd:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            logger.info(f"已关闭弹窗: hwnd={hwnd}")
            return True

        await asyncio.sleep(0.3)

    return False


class _Win32AuthContext:
    """handle_auth_dialog 的异步上下文管理器"""

    def __init__(self, username: str, password: str, timeout: float):
        self.username = username
        self.password = password
        self.timeout = timeout
        self._task: Optional[asyncio.Task] = None

    async def __aenter__(self):
        # 在后台启动弹窗监听任务
        self._task = asyncio.create_task(
            _fill_windows_auth_dialog(self.username, self.password, self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=self.timeout)
            except asyncio.TimeoutError:
                self._task.cancel()
                logger.warning("Windows 弹窗处理超时")
