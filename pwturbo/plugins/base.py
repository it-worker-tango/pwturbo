"""插件基类模块 - 定义插件接口，所有插件必须继承此类"""
from abc import ABC, abstractmethod


class Plugin(ABC):
    """
    插件基类，定义统一的插件接口。

    自定义插件示例：
        class MyPlugin(Plugin):
            def __init__(self):
                super().__init__("my_plugin")

            async def initialize(self):
                pass  # 初始化资源

            async def cleanup(self):
                pass  # 释放资源

        driver.use_plugin("my", MyPlugin())
    """

    def __init__(self, name: str):
        """
        初始化插件。

        参数：
            name: 插件唯一名称
        """
        self.name = name
        self.enabled = True

    @abstractmethod
    async def initialize(self):
        """初始化插件资源（连接数据库、创建目录等）"""
        pass

    @abstractmethod
    async def cleanup(self):
        """释放插件资源（关闭连接、保存数据等）"""
        pass

    def enable(self):
        """启用插件"""
        self.enabled = True

    def disable(self):
        """禁用插件（禁用后插件方法不执行任何操作）"""
        self.enabled = False

    def __repr__(self):
        status = "启用" if self.enabled else "禁用"
        return f"Plugin({self.name}, {status})"
