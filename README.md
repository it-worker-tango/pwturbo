# pwturbo

基于 Playwright 的多线程 Web 自动化框架，支持有头/无头模式动态切换、文件异步下载、OKTA SSO 认证，具备良好的可扩展性。

## 特性

- 多线程并发，支持同时运行多个独立浏览器会话
- 有头/无头模式运行时动态切换（自动保存 cookies）
- 登录后通过 requests 携带 cookies 调用 API
- 文件异步下载，大文件不阻塞主流程
- OKTA SSO 认证自动化（兼容真实 OKTA 和模拟环境）
- Windows 系统级弹窗处理（NTLM/Kerberos）
- 元素操作全封装，不直接暴露 Playwright 原生 API
- Page Object 基类，方便继承扩展
- 插件系统，支持截图管理、数据库存储等扩展
- YAML 配置文件支持

## 项目结构

```
pwturbo/
├── framework/              # 框架核心（打包发布的内容）
│   ├── core/
│   │   ├── driver.py       # WebDriver 统一入口（推荐使用）
│   │   ├── browser.py      # 浏览器管理
│   │   ├── page.py         # 页面操作 + requests 集成
│   │   ├── base_page.py    # Page Object 基类
│   │   └── downloader.py   # 文件异步下载
│   ├── elements/
│   │   └── element.py      # 元素操作封装
│   ├── auth/
│   │   └── okta.py         # OKTA SSO + Win32 弹窗处理
│   ├── plugins/
│   │   ├── base.py         # 插件基类
│   │   ├── screenshot.py   # 截图插件
│   │   └── database.py     # 数据库插件
│   └── utils/
│       ├── logger.py       # 日志配置
│       ├── config.py       # YAML 配置管理
│       └── wait.py         # 等待/重试工具
├── tests/                  # 测试用例
├── examples/               # 使用示例
├── test_site/              # Django 测试网站（含模拟 OKTA）
├── scripts/                # 安装脚本
├── dist/                   # 打包产物
├── config.yaml             # 配置文件模板
├── demo.py                 # 快速演示
└── pyproject.toml
```

## 安装

推荐使用 [uv](https://docs.astral.sh/uv/) 作为环境管理工具，速度快、依赖隔离干净。

```bash
# 安装 uv（如果还没有）
pip install uv

# 从 whl 文件安装（推荐）
uv pip install pwturbo-0.3.0-py3-none-any.whl

# 可选依赖
uv pip install "pwturbo-0.3.0-py3-none-any.whl[yaml]"   # YAML 配置支持
uv pip install "pwturbo-0.3.0-py3-none-any.whl[mfa]"    # TOTP/MFA 自动填写
uv pip install "pwturbo-0.3.0-py3-none-any.whl[all]"    # 全部可选依赖

# 安装 Playwright 浏览器
uv run playwright install chromium
```

> 也可以用 pip 安装，将上面的 `uv pip` 替换为 `pip` 即可。

## 快速开始

```python
import asyncio
from framework import WebDriver

async def main():
    async with WebDriver(headless=False) as driver:
        page = await driver.new_page()
        await page.goto("https://example.com/login")

        # 使用封装的元素操作
        await page.element("#username").fill("admin")
        await page.element("#password").fill("password")
        await page.element("button[type='submit']").click()

        # 登录后用 requests 调用 API
        await page.sync_cookies()
        resp = page.request_get("https://example.com/api/user/")
        print(resp.json())

asyncio.run(main())
```

## 核心用法

### Page Object 模式

```python
from framework import WebDriver, BasePage

class LoginPage(BasePage):
    @property
    def username(self):
        return self.element("#username")

    async def login(self, user, pwd):
        await self.username.fill(user)
        await self.element("#password").fill(pwd)
        await self.element("button[type='submit']").click()

async with WebDriver() as driver:
    page = await driver.new_page()
    login = LoginPage(page)
    await login.goto("https://example.com/login")
    await login.login("admin", "password")
```

### 多线程并发

```python
async def session_task(driver, user_id):
    page = await driver.new_page(context_id=f"user_{user_id}")
    await page.goto("https://example.com/login")
    # ...

async with WebDriver() as driver:
    results = await driver.run_concurrent(
        [session_task(driver, i) for i in range(5)],
        max_workers=3
    )
```

### 文件异步下载

```python
from framework import WebDriver, FileDownloader

async with WebDriver() as driver:
    page = await driver.new_page()
    # ... 登录 ...

    downloader = FileDownloader(download_dir="downloads")

    # 等待下载完成
    async with downloader.expect_download(page._page) as task_future:
        await page.element("#export-btn").click()
    task = await task_future
    await downloader.wait_for(task.task_id)
    print(f"已下载: {task.save_path}")

    # 或后台异步下载，不阻塞
    task_id = await downloader.start_background_download(page._page, "#export-btn")
    # 继续其他操作...
    await downloader.wait_for(task_id)
```

### OKTA SSO 认证

```python
from framework import WebDriver
from framework.auth import OktaHandler

async with WebDriver() as driver:
    page = await driver.new_page()
    okta = OktaHandler(username="user@company.com", password="pass")

    # 自动处理 OKTA 重定向和登录（兼容真实/模拟 OKTA）
    await okta.authenticate(page, app_url="https://app.company.com")
```

### 有头/无头模式切换

```python
async with WebDriver(headless=True) as driver:
    # 无头模式运行...
    await driver.switch_mode(headless=False)  # 切换为有头，浏览器窗口出现
    await driver.switch_mode(headless=True)   # 切回无头
```

### 插件扩展

```python
from framework import WebDriver
from framework.plugins.screenshot import ScreenshotPlugin
from framework.plugins.database import DatabasePlugin

async with WebDriver() as driver:
    driver.use_plugin("screenshot", ScreenshotPlugin("screenshots"))
    driver.use_plugin("db", DatabasePlugin("results/results.json"))

    await driver.get_plugin("screenshot").initialize()
    await driver.get_plugin("db").initialize()
    # ...
```

## 元素操作

```python
el = page.element("#selector")          # CSS（默认）
el = page.element("//input", "xpath")   # XPath
el = page.element("登录", "text")       # 文本内容
el = page.element("用户名", "label")    # 标签文本

await el.click()                        # 点击
await el.fill("text")                   # 填写
await el.type("text", delay=80)         # 模拟真人输入
await el.hover()                        # 悬停
await el.select_option(label="选项A")   # 下拉选择
await el.upload_file("file.pdf")        # 上传文件
text = await el.get_text()              # 获取文本
val  = await el.get_value()             # 获取输入框值
await el.wait_for_visible()             # 等待可见
await el.screenshot("el.png")          # 元素截图
```

## 配置文件

复制 `config.yaml` 到项目根目录按需修改：

```yaml
browser:
  type: chromium
  headless: true
  slow_mo: 0        # 调试时设为 500，方便观察

site:
  base_url: "https://your-app.com"

logging:
  level: "INFO"
  file: "logs/automation.log"
```

```python
async with WebDriver(config_path="config.yaml") as driver:
    ...
```

## 本地开发

```bash
# 克隆项目
git clone https://github.com/it-worker-tango/pwturbo.git
cd pwturbo

# 安装依赖（含开发依赖）
uv sync

# 安装 Playwright 浏览器
uv run playwright install chromium

# 启动测试网站
cd test_site
uv run python manage.py migrate
uv run python manage.py createsuperuser  # 用户名: admin 密码: admin123
uv run python manage.py runserver

# 运行测试（新终端）
uv run pytest tests/

# 打包
uv build
```

## 测试网站

`test_site/` 是一个 Django 应用，提供：

| 地址 | 说明 |
|------|------|
| `/accounts/login/` | 登录页 |
| `/dashboard/` | 登录后的控制台 |
| `/api/user/` | 用户信息 API |
| `/api/data/` | 测试数据 API |
| `/api/download/csv/` | CSV 文件下载 |
| `/api/download/json/` | JSON 文件下载 |
| `/okta/authorize/` | 模拟 OKTA 授权页 |
| `/okta/userinfo/` | 模拟 OKTA userinfo 接口 |

## 许可证

MIT License
