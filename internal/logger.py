import logging


def setup_logging(level: int = logging.INFO):
    """初始化全局日志配置"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
