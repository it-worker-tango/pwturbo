"""
文件下载模块 - 支持异步下载、自定义路径、进度回调和并发下载

核心设计：
- 通过 Playwright 的 download 事件监听触发下载
- 使用 asyncio 异步处理，大文件不阻塞主流程
- 支持下载队列，可同时管理多个下载任务
"""
import asyncio
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, List
from playwright.async_api import Page as PlaywrightPage, Download
from loguru import logger


class DownloadStatus(Enum):
    """下载状态枚举"""
    等待中 = "waiting"
    下载中 = "downloading"
    已完成 = "completed"
    失败 = "failed"
    已取消 = "cancelled"


@dataclass
class DownloadTask:
    """单个下载任务的信息"""
    task_id: str                          # 任务唯一 ID
    url: str                              # 下载来源 URL（触发下载的页面 URL）
    save_path: str                        # 文件保存路径
    status: DownloadStatus = DownloadStatus.等待中
    file_size: int = 0                    # 文件大小（字节），-1 表示未知
    downloaded: int = 0                   # 已下载字节数
    start_time: float = 0.0              # 开始时间戳
    end_time: float = 0.0                # 完成时间戳
    error: str = ""                       # 失败原因
    _download_obj: Optional[Download] = field(default=None, repr=False)  # Playwright Download 对象

    @property
    def duration(self) -> float:
        """下载耗时（秒）"""
        if self.end_time and self.start_time:
            return round(self.end_time - self.start_time, 2)
        return 0.0

    @property
    def is_done(self) -> bool:
        """是否已完成（成功或失败）"""
        return self.status in (DownloadStatus.已完成, DownloadStatus.失败, DownloadStatus.已取消)


class FileDownloader:
    """
    文件下载管理器。

    支持：
    - 异步下载（不阻塞主流程）
    - 自定义下载目录
    - 下载进度回调
    - 并发多文件下载
    - 等待下载完成

    使用示例：
        downloader = FileDownloader(download_dir="downloads")

        # 方式一：监听并等待下载完成
        async with downloader.expect_download(page) as task_future:
            await page.element("#download-btn").click()
        task = await task_future
        print(f"下载完成: {task.save_path}")

        # 方式二：后台异步下载，不等待
        await downloader.start_background_download(page, "#download-btn")
        # 继续其他操作...
        await downloader.wait_all()  # 最后统一等待
    """

    def __init__(
        self,
        download_dir: str = "downloads",
        timeout: float = 300.0,
        on_complete: Callable[[DownloadTask], None] = None,
        on_progress: Callable[[DownloadTask], None] = None,
    ):
        """
        初始化下载管理器。

        参数：
            download_dir: 默认下载目录
            timeout: 单个文件下载超时时间（秒），默认 5 分钟
            on_complete: 下载完成回调函数，接收 DownloadTask 参数
            on_progress: 下载进度回调函数（暂由完成事件触发）
        """
        self.download_dir = download_dir
        self.timeout = timeout
        self.on_complete = on_complete
        self.on_progress = on_progress

        self._tasks: Dict[str, DownloadTask] = {}
        self._background_tasks: List[asyncio.Task] = []

        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"下载管理器已初始化，下载目录: {download_dir}")

    def _make_task_id(self) -> str:
        """生成唯一任务 ID"""
        return f"dl_{int(time.time() * 1000)}"

    def _resolve_path(self, filename: str, sub_dir: str = None) -> str:
        """
        解析最终保存路径。

        参数：
            filename: 文件名
            sub_dir: 子目录（可选），用于分类存储
        """
        base = os.path.join(self.download_dir, sub_dir) if sub_dir else self.download_dir
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    async def _handle_download(
        self,
        download: Download,
        task_id: str,
        custom_path: str = None,
        sub_dir: str = None,
    ) -> DownloadTask:
        """
        处理 Playwright Download 对象，保存文件到指定路径。

        参数：
            download: Playwright Download 实例
            task_id: 任务 ID
            custom_path: 完整自定义路径（优先级最高）
            sub_dir: 子目录名
        """
        task = self._tasks[task_id]
        task.status = DownloadStatus.下载中
        task.start_time = time.time()
        task._download_obj = download

        # 确定保存路径
        suggested_name = download.suggested_filename or f"file_{task_id}"
        if custom_path:
            save_path = custom_path
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
        else:
            save_path = self._resolve_path(suggested_name, sub_dir)

        task.save_path = save_path
        logger.info(f"[{task_id}] 开始下载: {suggested_name} → {save_path}")

        try:
            # 异步等待下载完成并保存
            await asyncio.wait_for(
                download.save_as(save_path),
                timeout=self.timeout
            )

            task.status = DownloadStatus.已完成
            task.end_time = time.time()

            # 获取文件大小
            if os.path.exists(save_path):
                task.file_size = os.path.getsize(save_path)
                size_str = self._format_size(task.file_size)
            else:
                size_str = "未知"

            logger.info(
                f"[{task_id}] 下载完成: {suggested_name} "
                f"大小={size_str} 耗时={task.duration}s"
            )

            # 触发完成回调
            if self.on_complete:
                self.on_complete(task)

        except asyncio.TimeoutError:
            task.status = DownloadStatus.失败
            task.end_time = time.time()
            task.error = f"下载超时（>{self.timeout}s）"
            logger.error(f"[{task_id}] 下载超时: {suggested_name}")

        except Exception as e:
            task.status = DownloadStatus.失败
            task.end_time = time.time()
            task.error = str(e)
            logger.error(f"[{task_id}] 下载失败: {e}")

        return task

    def expect_download(
        self,
        page: 'PlaywrightPage',
        custom_path: str = None,
        sub_dir: str = None,
    ):
        """
        返回一个异步上下文管理器，用于监听并等待下载完成。

        在 async with 块内触发下载操作（如点击下载按钮），
        退出 async with 后可 await 获取下载任务结果。

        参数：
            page: Playwright Page 实例（原生）
            custom_path: 自定义完整保存路径
            sub_dir: 子目录名，用于分类存储

        使用示例：
            async with downloader.expect_download(page._page) as task_future:
                await page.element("#download-btn").click()
            task = await task_future
            print(f"文件已保存到: {task.save_path}")
        """
        return _DownloadContext(self, page, custom_path, sub_dir)

    async def start_background_download(
        self,
        page: 'PlaywrightPage',
        trigger_selector: str,
        custom_path: str = None,
        sub_dir: str = None,
    ) -> str:
        """
        后台异步下载 - 点击触发元素后立即返回，下载在后台进行。

        适合大文件下载，不阻塞后续操作。

        参数：
            page: Playwright Page 实例（原生）
            trigger_selector: 触发下载的元素 CSS 选择器
            custom_path: 自定义保存路径
            sub_dir: 子目录名

        返回：
            任务 ID，可用于后续查询状态

        使用示例：
            task_id = await downloader.start_background_download(
                page._page, "#export-btn", sub_dir="reports"
            )
            # 继续其他操作...
            await downloader.wait_for(task_id)  # 需要时再等待
        """
        task_id = self._make_task_id()
        task = DownloadTask(task_id=task_id, url=page.url, save_path="")
        self._tasks[task_id] = task

        async def _run():
            async with page.expect_download() as download_info:
                await page.click(trigger_selector)
            download = await download_info.value
            await self._handle_download(download, task_id, custom_path, sub_dir)

        bg_task = asyncio.create_task(_run())
        self._background_tasks.append(bg_task)
        logger.info(f"[{task_id}] 后台下载任务已启动")
        return task_id

    async def wait_for(self, task_id: str, poll_interval: float = 0.5) -> DownloadTask:
        """
        等待指定任务完成。

        参数：
            task_id: 任务 ID
            poll_interval: 轮询间隔（秒）

        返回：
            完成的 DownloadTask
        """
        if task_id not in self._tasks:
            raise ValueError(f"任务不存在: {task_id}")

        while not self._tasks[task_id].is_done:
            await asyncio.sleep(poll_interval)

        return self._tasks[task_id]

    async def wait_all(self) -> List[DownloadTask]:
        """
        等待所有后台下载任务完成。

        返回：
            所有任务列表
        """
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()

        completed = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.已完成)
        failed = sum(1 for t in self._tasks.values() if t.status == DownloadStatus.失败)
        logger.info(f"所有下载任务完成: 成功={completed}, 失败={failed}")
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """获取任务信息"""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[DownloadTask]:
        """获取所有任务列表"""
        return list(self._tasks.values())

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """将字节数格式化为可读字符串"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


class _DownloadContext:
    """expect_download 的异步上下文管理器实现"""

    def __init__(self, downloader: FileDownloader, page, custom_path, sub_dir):
        self._downloader = downloader
        self._page = page
        self._custom_path = custom_path
        self._sub_dir = sub_dir
        self._task_id = downloader._make_task_id()
        self._expect_cm = None          # Playwright expect_download 上下文管理器
        self._expect_info = None        # __aenter__ 返回的 EventInfo 对象
        self._future: Optional[asyncio.Future] = None

    async def __aenter__(self):
        # 注册任务
        task = DownloadTask(task_id=self._task_id, url="", save_path="")
        self._downloader._tasks[self._task_id] = task

        # 启动 Playwright 的 expect_download 上下文，保存返回的 info 对象
        self._expect_cm = self._page.expect_download()
        self._expect_info = await self._expect_cm.__aenter__()

        # 返回一个 future，退出 with 块后可 await 获取结果
        loop = asyncio.get_event_loop()
        self._future = loop.create_future()
        return self._future

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self._expect_cm.__aexit__(exc_type, exc_val, exc_tb)
            return False

        # 退出 Playwright 的 expect_download 上下文，触发等待
        await self._expect_cm.__aexit__(None, None, None)

        # 从 info 对象上获取 Download 实例
        download = await self._expect_info.value

        # 异步处理下载，完成后设置 future 结果
        async def _resolve():
            result = await self._downloader._handle_download(
                download, self._task_id, self._custom_path, self._sub_dir
            )
            if not self._future.done():
                self._future.set_result(result)

        asyncio.create_task(_resolve())
