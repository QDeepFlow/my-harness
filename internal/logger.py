import logging


def setup_logging(level: int = logging.INFO, fmt: str = '%(asctime)s - %(levelname)s - %(message)s'):
    """初始化全局日志配置"""
    logging.basicConfig(level=level, format=fmt)

