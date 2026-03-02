"""数据库插件 - 用于存储测试结果和测试数据"""
import json
import os
import time
from loguru import logger
from pwturbo.plugins.base import Plugin


class DatabasePlugin(Plugin):
    """
    数据库插件，支持将测试结果持久化存储。

    当前实现使用 JSON 文件存储（轻量级，无需额外依赖）。
    可扩展为 SQLite、MySQL、PostgreSQL 等数据库。

    使用示例：
        db = DatabasePlugin("results/test_results.json")
        driver.use_plugin("db", db)
        await db.initialize()

        # 保存测试结果
        await db.save_result({
            "test": "login_test",
            "status": "passed",
            "duration": 2.5,
        })

        # 查询结果
        results = await db.get_results()
    """

    def __init__(self, file_path: str = "results/test_results.json"):
        """
        初始化数据库插件。

        参数：
            file_path: 结果文件路径（JSON 格式）
        """
        super().__init__("database")
        self.file_path = file_path
        self._results = []

    async def initialize(self):
        """初始化存储目录和文件"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # 加载已有数据
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._results = json.load(f)
                logger.info(f"数据库插件已加载 {len(self._results)} 条历史记录: {self.file_path}")
            except Exception as e:
                logger.warning(f"加载历史记录失败: {e}，将创建新文件")
                self._results = []
        else:
            logger.info(f"数据库插件已初始化: {self.file_path}")

    async def cleanup(self):
        """保存数据并关闭"""
        await self._save()
        logger.info(f"数据库插件已关闭，共保存 {len(self._results)} 条记录")

    async def save_result(self, data: dict):
        """
        保存一条测试结果。

        参数：
            data: 结果数据字典，会自动添加时间戳

        使用示例：
            await db.save_result({
                "test_name": "test_login",
                "status": "passed",
                "url": "http://localhost:8000/dashboard/",
                "duration": 2.3,
            })
        """
        if not self.enabled:
            return

        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            **data
        }
        self._results.append(record)
        await self._save()
        logger.debug(f"已保存测试结果: {record}")

    async def get_results(self, status: str = None) -> list:
        """
        查询测试结果。

        参数：
            status: 按状态过滤，如 "passed" / "failed"，None 返回全部

        返回：
            结果列表
        """
        if status:
            return [r for r in self._results if r.get("status") == status]
        return self._results.copy()

    async def clear(self):
        """清空所有记录"""
        self._results = []
        await self._save()
        logger.info("数据库记录已清空")

    async def _save(self):
        """将数据写入 JSON 文件"""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
