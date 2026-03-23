import shutil
import os
import pygetwindow as gw
import pytest
from pywinauto import Application

from base.pywinauto_base import PywinautoBase
from logging_config import logger
from utils.tools import clear_files_in_directory

# ===================== 核心配置=====================
SOFTWARE_EXE_PATH = r"D:\Desktop\EpdAnalysis_4.1.1.11\bin\EpdAnalysis.exe"  # 修正大小写
MAIN_WINDOW_TITLE = "EpdAnalysis"  # 模糊匹配标题关键字
START_TIMEOUT = 30  # 启动超时（秒）
BACKEND = "uia"  # 后端类型：uia / win32
DEFAULT_CONTROL_TIMEOUT = 30


def __init__(self):
    self.app = None
    self.main_window = None


@pytest.fixture(scope="session")
def app():
    """连接到已运行的应用程序，并确保窗口可见"""
    try:
        # 尝试查找应用程序窗口(使用pygetwindow)
        # sleep(5)
        # app = Application(backend=BACKEND).start(SOFTWARE_EXE_PATH)
        app = Application(backend=BACKEND).connect(title_re=MAIN_WINDOW_TITLE)
        windows = gw.getWindowsWithTitle(MAIN_WINDOW_TITLE)
        if not windows:
            pytest.fail(f"未找到标题匹配的窗口: {MAIN_WINDOW_TITLE}")
        window = windows[0]
        # 如果窗口最小化，则恢复它
        if window.isMinimized:
            window.restore()
            # 等待窗口恢复(可根据实际情况调整等待时间)
            import time
            time.sleep(0.1)

        # 获取主窗口并确保它处于活动状态
        main_window = app.window(title_re=MAIN_WINDOW_TITLE)
        logger.info(f"成功连接到应用程序，窗口句柄: {main_window.handle}")
        main_window.set_focus()
        yield app
    except Exception as e:
        pytest.fail(f"连接应用程序失败: {str(e)}")
        logger.error(f"连接应用程序失败: {str(e)}")


# 主窗口fixture，使用app fixture
@pytest.fixture(scope="function")
def main_window(app):
    """获取主窗口并设置焦点"""
    try:
        window = app.window(title_re=MAIN_WINDOW_TITLE)
        window.set_focus()
        yield window
    except Exception as e:
        pytest.fail(f"获取主窗口失败: {str(e)}")


@pytest.fixture(scope="function")
def pywinauto_base(main_window):
    """创建Pywinauto_Base实例"""
    return PywinautoBase(main_window)


def clear_allure_results(session):
    """仅在session首次调用时清理，后续跳过"""
    # 检查session是否有"已清理"的标记，没有则执行清理
    if not hasattr(session, "is_cleaned"):
        # 1. 清理allure-results目录
        allure_dir = "allure-results"
        if os.path.exists(allure_dir):
            shutil.rmtree(allure_dir)
            logger.info(f"已清理旧的 allure-results 目录: {allure_dir}")
        os.makedirs(allure_dir, exist_ok=True)
        print(f"已重建 allure-results 目录: {allure_dir}")
        # 标记为已清理，避免重复执行
        session.is_cleaned = True
    else:
        logger.info("非首次执行，跳过清理")


# ===== 挂载钩子：把session传入清理函数 =====
def pytest_sessionstart(session):
    logger.info("===== 测试会话开始，检查清理状态 =====")
    clear_allure_results(session)  # 传入session对象

    """初始化CSV对比统计数据（绑定到session对象）"""
    session.compare_stats = {
        "total_files": 0,
        "success_files": 0,
        "failed_files": 0,
        "failed_details": {}
    }
    # 从环境变量获取循环次数
    session.loop_count = os.getenv("LOOP_COUNT", "1")


def pytest_configure(config):
    # 注册自定义标记，添加清晰的注释说明
    config.addinivalue_line(
        "markers",
        "no_allure_report: 执行用例但不生成Allure报告（用于指定无需报告的用例）"
    )
