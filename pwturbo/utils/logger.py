"""日志配置模块 - 基于 loguru，支持控制台彩色输出和文件滚动日志"""
import os
import sys
from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: str = "logs/automation.log",
    rotation: str = "10 MB",
    retention: str = "7 days",
    colorize: bool = True,
) -> logger:
    """
    配置全局日志。

    参数：
        level: 日志级别，DEBUG / INFO / WARNING / ERROR
        log_file: 日志文件路径，None 则不写文件
        rotation: 日志文件滚动策略，如 "10 MB" / "1 day" / "00:00"
        retention: 日志保留时长，如 "7 days" / "1 month"
        colorize: 控制台是否彩色输出

    返回：
        配置好的 logger 实例
    """
    # 移除默认 handler
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 文件输出格式（不含颜色标签）
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # 添加控制台 handler
    logger.add(
        sys.stderr,
        level=level,
        format=console_format,
        colorize=colorize,
    )

    # 添加文件 handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logger.add(
            log_file,
            level=level,
            format=file_format,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
        )

    return logger
