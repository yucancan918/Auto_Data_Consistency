import logging
import os
from datetime import datetime
from typing import Optional

# 全局日志器名称（确保所有模块使用同一个日志器）
GLOBAL_LOGGER_NAME = "auto_test_logger"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的日志器（确保全局只初始化一次）
    :param name: 模块名称（可选，用于区分不同模块的日志）
    :return: 配置好的logger对象
    """
    # 1. 获取全局日志器（所有模块共享同一个根日志器）
    root_logger = logging.getLogger(GLOBAL_LOGGER_NAME)

    # 2. 如果已初始化（已有处理器），直接返回子日志器（带模块名）
    if root_logger.handlers:
        return logging.getLogger(f"{GLOBAL_LOGGER_NAME}.{name}") if name else root_logger

    # 3. 未初始化则配置日志（只执行一次）
    root_logger.setLevel(logging.INFO)  # 全局日志级别

    # 3.1 创建日志目录（当前文件所在目录下的logs文件夹）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(current_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 3.2 生成日志文件名（带时间戳，确保每次运行一个文件）
    log_file = os.path.join(
        log_dir,
        f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    # 3.3 定义日志格式（包含模块名，方便区分来源）
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s"
    )

    # 3.4 添加文件处理器（写入日志文件）
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)  # 文件日志级别
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 3.5 添加控制台处理器（实时输出到控制台）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台日志级别
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 4. 返回带模块名的子日志器（方便定位日志来源）
    if name:
        return logging.getLogger(f"{GLOBAL_LOGGER_NAME}.{name}")
    return root_logger


# 全局默认日志器（可直接导入使用，自动关联模块名）
logger = get_logger()