"""等待工具模块 - 提供智能等待、条件等待和重试机制"""
import asyncio
import time
from typing import Callable, Any, Optional
from loguru import logger


async def wait_until(
    condition: Callable,
    timeout: float = 10.0,
    interval: float = 0.5,
    error_msg: str = "等待超时"
) -> Any:
    """
    等待直到条件函数返回真值。

    参数：
        condition: 异步或同步的条件函数，返回真值时停止等待
        timeout: 最大等待时间（秒）
        interval: 检查间隔（秒）
        error_msg: 超时时的错误信息

    返回：
        条件函数的返回值

    使用示例：
        # 等待元素出现
        await wait_until(
            lambda: page.element("#result").is_visible(),
            timeout=10,
            error_msg="结果元素未出现"
        )
    """
    start = time.time()

    while True:
        try:
            if asyncio.iscoroutinefunction(condition):
                result = await condition()
            else:
                result = condition()

            if result:
                return result
        except Exception:
            pass

        elapsed = time.time() - start
        if elapsed >= timeout:
            raise TimeoutError(f"{error_msg}（已等待 {elapsed:.1f}s）")

        await asyncio.sleep(interval)


async def retry(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    error_msg: str = None
) -> Any:
    """
    带重试机制的函数执行器。

    参数：
        func: 要执行的异步函数
        max_attempts: 最大重试次数
        delay: 每次重试前的等待时间（秒）
        exceptions: 触发重试的异常类型
        error_msg: 自定义错误信息前缀

    返回：
        函数执行结果

    使用示例：
        result = await retry(
            lambda: page.element("#btn").click(),
            max_attempts=3,
            delay=1.0
        )
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_error = e
            if attempt < max_attempts:
                prefix = error_msg or "操作"
                logger.warning(f"{prefix} 第 {attempt}/{max_attempts} 次失败: {e}，{delay}s 后重试...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"已达最大重试次数 ({max_attempts})，最终失败: {e}")

    raise last_error


async def sleep(seconds: float, reason: str = None):
    """
    带日志的等待函数（替代 asyncio.sleep）。

    参数：
        seconds: 等待秒数
        reason: 等待原因（用于日志）
    """
    if reason:
        logger.debug(f"等待 {seconds}s: {reason}")
    await asyncio.sleep(seconds)


def retry_decorator(max_attempts: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """
    重试装饰器，用于装饰异步函数。

    使用示例：
        @retry_decorator(max_attempts=3, delay=0.5)
        async def click_button(page):
            await page.element("#btn").click()
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await retry(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                delay=delay,
                exceptions=exceptions,
                error_msg=func.__name__
            )
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
