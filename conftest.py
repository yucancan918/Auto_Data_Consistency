import shutil
import os
import json
import pygetwindow as gw
import pytest
from pywinauto import Application

from base.pywinauto_base import PywinautoBase
from logging_config import logger
from utils.tools import clear_files_in_directory

# ===================== 核心配置=====================
# SOFTWARE_EXE_PATH = r"D:\Desktop\EpdAnalysis_4.2.1.1\bin\EpdAnalysis.exe"  # 旧分析软件
SOFTWARE_EXE_PATH = r"D:\Desktop\software_test\analysis\EpdAnalysis_5.0.0(测试DA3.3V1接口)\bin\EpdAnalysis.exe"  # 新分析软件
MAIN_WINDOW_TITLE = "EpdAnalysis"  # 模糊匹配标题关键字
START_TIMEOUT = 30  # 启动超时（秒）
BACKEND = "uia"  # 后端类型：uia / win32
DEFAULT_CONTROL_TIMEOUT = 30


def __init__(self):
    self.app = None
    self.main_window = None

#
# @pytest.fixture(scope="session")
# def app():
#     """连接到已运行的应用程序，并确保窗口可见"""
#     try:
#         # 尝试查找应用程序窗口(使用pygetwindow)
#         # sleep(5)
#         # app = Application(backend=BACKEND).start(SOFTWARE_EXE_PATH)
#         app = Application(backend=BACKEND).connect(title_re=MAIN_WINDOW_TITLE)
#         windows = gw.getWindowsWithTitle(MAIN_WINDOW_TITLE)
#         if not windows:
#             pytest.fail(f"未找到标题匹配的窗口: {MAIN_WINDOW_TITLE}")
#         window = windows[0]
#         # 如果窗口最小化，则恢复它
#         if window.isMinimized:
#             window.restore()
#             # 等待窗口恢复(可根据实际情况调整等待时间)
#             import time
#             time.sleep(0.1)
#
#         # 获取主窗口并确保它处于活动状态
#         main_window = app.window(title_re=MAIN_WINDOW_TITLE)
#         logger.info(f"成功连接到应用程序，窗口句柄: {main_window.handle}")
#         main_window.set_focus()
#         yield app
#     except Exception as e:
#         pytest.fail(f"连接应用程序失败: {str(e)}")
#         logger.error(f"连接应用程序失败: {str(e)}")
@pytest.fixture(scope="session")
def app():
    """连接到已运行的应用程序，并确保窗口可见 —— 纯 pywinauto 版本"""
    try:
        # 1. 直接用 pywinauto 连接，不要用 pygetwindow
        app = Application(backend=BACKEND).connect(
            title_re=MAIN_WINDOW_TITLE,
            timeout=START_TIMEOUT,  # 直接在这里加等待时间
            class_name="MainWindow"
        )

        # 2. 只用 pywinauto 操作窗口：恢复 + 激活
        main_window = app.window(title_re=MAIN_WINDOW_TITLE)
        main_window.wait("visible", timeout=60)  # 等待可见

        # 如果最小化，恢复
        if main_window.is_minimized():
            main_window.restore()

        # 激活窗口
        main_window.set_focus()

        logger.info(f"✅ 成功连接应用，窗口句柄: {main_window.handle}")
        yield app

    except Exception as e:
        logger.error(f"❌ 连接应用失败: {str(e)}")
        pytest.fail(f"连接应用程序失败: {str(e)}")
# 主窗口fixture，使用app fixture
# @pytest.fixture(scope="function")
# def main_window(app):
#     """获取主窗口并设置焦点"""
#     try:
#         window = app.window(title_re=MAIN_WINDOW_TITLE)
#         window.wait("ready", timeout=300)
#         window.set_focus()
#         yield window
#     except Exception as e:
#         pytest.fail(f"获取主窗口失败: {str(e)}")

@pytest.fixture(scope="function")
def main_window(app):
    """获取主窗口并设置焦点"""
    try:
        window = app.window(title_re=MAIN_WINDOW_TITLE)
        # 等待窗口 可用 + 可见
        window.wait("visible", timeout=60)
        window.wait("enabled", timeout=60)
        # 等待 UI 渲染完成（最关键！）
        window.wait("ready", timeout=60)
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

    # 清空上一轮残留的CSV差异收集结果（防止跨轮/跨session串数据）
    _failed_compare_results.clear()

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


# ===== 收集CSV对比失败明细，供存档summary.txt列出差异CSV及详细差异 =====
DIFF_RESULT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "diff_result.json"
)

_failed_compare_results = []


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """在用例执行阶段结束后，捕获CSV对比失败的用例名与差异明细"""
    outcome = yield
    report = outcome.get_result()

    if call.when != "call" or not report.failed:
        return

    # 仅收集CSV对比用例（参数化参数名为 csv_name）
    csv_name = None
    callspec = getattr(item, "callspec", None)
    if callspec is not None:
        csv_name = callspec.params.get("csv_name")

    if not csv_name:
        return

    # 提取断言消息（不含完整堆栈）：即"CSV存在N处不一致：..."整段差异明细
    detail = ""
    longrepr = getattr(report, "longrepr", None)
    if longrepr is not None:
        reprcrash = getattr(longrepr, "reprcrash", None)
        if reprcrash is not None and getattr(reprcrash, "message", None):
            detail = reprcrash.message
        else:
            detail = str(longrepr)

    # 去掉可能的"AssertionError: "前缀，让存档更干净
    if detail.startswith("AssertionError: "):
        detail = detail[len("AssertionError: "):]

    _failed_compare_results.append({"csv_name": csv_name, "detail": detail})


def pytest_sessionfinish(session, exitstatus):
    """会话结束时，把本轮CSV差异明细写入文件，供main.py存档时读取"""
    data = {"failed_files": _failed_compare_results}
    try:
        with open(DIFF_RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(
            f"已写入CSV差异明细文件：{DIFF_RESULT_FILE}，失败CSV：{len(_failed_compare_results)} 个"
        )
    except Exception as e:
        logger.error(f"写入CSV差异明细文件失败：{e}")