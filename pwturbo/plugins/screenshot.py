"""截图插件 - 自动管理截图，支持失败自动截图"""
import os
import time
from loguru import logger
from pwturbo.plugins.base import Plugin


class ScreenshotPlugin(Plugin):
    """
    截图管理插件。

    功能：
    - 自动按时间戳命名截图
    - 支持失败时自动截图
    - 截图分类存储（成功/失败）

    使用示例：
        driver.use_plugin("screenshot", ScreenshotPlugin("screenshots"))

        # 在测试中使用
        plugin = driver.get_plugin("screenshot")
        await plugin.capture(page, "登录成功")
    """

    def __init__(self, base_dir: str = "screenshots"):
        """
        初始化截图插件。

        参数：
            base_dir: 截图根目录
        """
        super().__init__("screenshot")
        self.base_dir = base_dir
        self._count = 0

    async def initialize(self):
        """初始化截图目录"""
        os.makedirs(f"{self.base_dir}/success", exist_ok=True)
        os.makedirs(f"{self.base_dir}/failure", exist_ok=True)
        logger.info(f"截图插件已初始化，目录: {self.base_dir}")

    async def cleanup(self):
        """清理（无需操作）"""
        logger.info(f"截图插件已关闭，共截图 {self._count} 张")

    async def capture(self, page, name: str = None, success: bool = True) -> str:
        """
        截取页面截图并保存。

        参数：
            page: Page 封装实例
            name: 截图名称（不含扩展名），不传则使用时间戳
            success: True=保存到 success 目录，False=保存到 failure 目录

        返回：
            截图文件路径
        """
        if not self.enabled:
            return ""

        category = "success" if success else "failure"
        timestamp = int(time.time())
        filename = f"{name}_{timestamp}" if name else str(timestamp)
        # 替换文件名中的非法字符
        filename = filename.replace(" ", "_").replace("/", "_")
        path = f"{self.base_dir}/{category}/{filename}.png"

        result = await page.screenshot(path=path)
        self._count += 1
        logger.info(f"截图已保存 [{category}]: {path}")
        return result

    async def capture_on_failure(self, page, test_name: str = "unknown") -> str:
        """
        失败时自动截图（在 except 块中调用）。

        参数：
            page: Page 封装实例
            test_name: 测试名称，用于文件命名
        """
        return await self.capture(page, f"FAIL_{test_name}", success=False)
