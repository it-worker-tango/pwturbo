"""配置管理模块 - 支持 YAML 配置文件，提供默认值回退"""
import os
from typing import Any
from loguru import logger


class Config:
    """
    配置管理类，支持从 YAML 文件加载配置，并支持点号路径访问。

    使用示例：
        config = Config("config.yaml")
        headless = config.get("browser.headless", True)
        base_url = config.get("site.base_url", "http://localhost:8000")
    """

    def __init__(self, config_path: str = None):
        """
        初始化配置。

        参数：
            config_path: YAML 配置文件路径，不传则使用空配置
        """
        self._data = {}

        if config_path and os.path.exists(config_path):
            self._load(config_path)
        elif config_path:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")

    def _load(self, path: str):
        """加载 YAML 配置文件"""
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
            logger.info(f"配置文件已加载: {path}")
        except ImportError:
            logger.warning("未安装 PyYAML，跳过配置文件加载。可运行: uv add pyyaml")
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        通过点号路径获取配置值。

        参数：
            key: 配置路径，如 "browser.headless" 或 "site.base_url"
            default: 找不到时的默认值

        返回：
            配置值或默认值
        """
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        动态设置配置值（仅在内存中生效，不写入文件）。

        参数：
            key: 配置路径
            value: 配置值
        """
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def all(self) -> dict:
        """返回所有配置的字典"""
        return self._data.copy()
