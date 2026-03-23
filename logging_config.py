import logging
import os
from datetime import datetime


def get_logger(name: str, log_file: str = None) -> logging.Logger:
    """
    获取配置好的日志器
    :param name: 日志器名称（通常用 __name__）
    :param log_file: 日志文件路径（None则只输出到控制台）
    :return: 配置好的logger对象
    """
    # 1. 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # 全局日志级别（最低级别）

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 2. 定义日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )

    # 3. 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台输出INFO及以上级别
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 4. 可选：添加文件处理器（如果指定了log_file）
    if log_file:
        # 创建日志目录（如果不存在）
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 文件输出DEBUG及以上级别（更详细）
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局默认日志器（可直接导入使用）
logger = get_logger(__name__)