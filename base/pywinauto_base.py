import io
import traceback

import allure
from pywinauto import Desktop, ElementNotFoundError, keyboard
from pywinauto.base_wrapper import BaseWrapper
from pywinauto.controls.uia_controls import ButtonWrapper
from pywinauto.timings import TimeoutError, wait_until_passes
import pytest
import time
from pywinauto.application import Application
import pygetwindow as gw
from path_config.path import CONSOLE_PATH, CONSOLE_TITLE, ANALYSIS_TITLE, ANALYSIS_PATH
from tests.logging_config import logger



class PywinautoBase:
    """所有测试类的基类，提供常用的UI操作方法"""

    def __init__(self, window):
        """初始化测试基类，传入主窗口对象"""
        self.window = window
        self.desktop = Desktop(backend="uia")  # 初始化桌面对象
        logger.info(f"PywinautoBase初始化完成，主窗口: {window}")

    def get_window(self):
        return self.window

    def launch_console(self):
        """启动Console软件，返回主窗口对象"""
        try:
            # 启动应用程序
            self.console_app = Application(backend="uia").start(CONSOLE_PATH, timeout=20)
            time.sleep(2)  # 等待启动

            # 查找窗口
            windows = gw.getWindowsWithTitle(CONSOLE_TITLE)
            if not windows:
                raise Exception(f"未找到Console窗口: {CONSOLE_TITLE}")
            window = windows[0]
            if window.isMinimized:
                window.restore()
                time.sleep(0.1)
            # 连接应用并获取主窗口
            self.console_app = Application(backend="uia").connect(title_re=CONSOLE_TITLE, timeout=10)
            self.window = self.console_app.window(title_re=CONSOLE_TITLE)
            self.window.set_focus()
            logger.info("Console软件启动成功")
            return self.window  # 返回窗口对象供外部使用
        except Exception as e:
            error_msg = f"启动Console失败: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)
            raise  # 抛出异常，中断测试

    # def set_address_path(self, new_path, main_window):
    #     """
    #     精准操作地址栏输入新路径（最终修复版）
    #     :param new_path: 目标路径，如 r"D:\Esp_DataSet\Project"
    #     :param main_window: pywinauto的uia后端WindowSpecification对象
    #     """
    #     try:
    #         # ===================== 关键修复1：区分WindowSpecification和UIAWrapper =====================
    #         # 1. main_window是WindowSpecification，用child_window()定位选择文档窗口（返回WindowSpecification）
    #         select_window_spec = main_window.child_window(title="选择文档", control_type="Window")
    #         if not select_window_spec.exists(timeout=5):
    #             raise ElementNotFoundError("未找到“选择文档”窗口")
    #
    #         # 2. 获取UIAWrapper控件对象（只能用children/descendants找子控件，不能用child_window）
    #         select_window = select_window_spec.wrapper_object()
    #         select_window.set_focus()
    #         time.sleep(0.5)
    #
    #         # 3. 找地址栏容器（UIAWrapper用descendants筛选，不用child_window）
    #         # 筛选条件：auto_id=41477 + control_type=Pane
    #         address_panes = select_window.descendants(
    #             auto_id="41477",
    #             control_type="Pane"
    #         )
    #         if not address_panes:
    #             raise ElementNotFoundError("未找到地址栏容器（auto_id=41477）")
    #         address_pane = address_panes[0]  # 取第一个匹配的Pane
    #
    #         # 4. 找地址栏Toolbar（用descendants筛选标题以“地址:”开头的Toolbar）
    #         address_toolbars = address_pane.descendants(
    #             title_re=r"地址:.*",  # 正则匹配地址栏标题，避免转义
    #             control_type="ToolBar"
    #         )
    #         if not address_toolbars:
    #             # 备选：不筛选标题，取地址栏容器内第一个Toolbar
    #             address_toolbars = address_pane.descendants(control_type="ToolBar")
    #             if not address_toolbars:
    #                 raise ElementNotFoundError("地址栏容器内未找到Toolbar控件")
    #         address_toolbar = address_toolbars[0]
    #
    #         # ===================== 关键修复2：稳定激活地址栏输入 =====================
    #         # 模拟人工点击地址栏文本区域（坐标根据Toolbar大小调整）
    #         address_toolbar.click_input(coords=(150, 10))  # 真实鼠标点击，最稳定
    #         time.sleep(0.3)
    #         address_toolbar.click_input(coords=(150, 10))  # 第二次点击选中全部路径
    #         time.sleep(0.3)
    #
    #         # ===================== 关键修复3：路径输入（避免转义） =====================
    #         # 清空原有路径
    #         keyboard.send_keys("^a", with_spaces=True)
    #         time.sleep(0.2)
    #         keyboard.send_keys("{BACKSPACE}", with_spaces=True)
    #         time.sleep(0.2)
    #
    #         # 输入新路径（强制转成原始字符串，避免转义问题）
    #         raw_new_path = r"{}".format(new_path)
    #         keyboard.send_keys(raw_new_path, with_spaces=True)
    #         time.sleep(0.2)
    #
    #         # 回车确认
    #         keyboard.send_keys("{ENTER}", with_spaces=True)
    #
    #         time.sleep(1)
    #         print(f"✅ 成功跳转到路径: {raw_new_path}")
    #
    #     except ElementNotFoundError as e:
    #         print(f"❌ 控件定位失败: {str(e)}")
    #         traceback.print_exc()
    #     except Exception as e:
    #         print(f"❌ 操作地址栏失败: {str(e)}")
    #         traceback.print_exc()
    def launch_analysis(self):
        """启动Analysis软件，返回主窗口对象（普通方法，非fixture）"""
        try:
            self.analysis_app = Application(backend="uia").start(ANALYSIS_PATH, timeout=20)
            time.sleep(2)

            windows = gw.getWindowsWithTitle(ANALYSIS_TITLE)
            if not windows:
                raise Exception(f"未找到Analysis窗口: {ANALYSIS_TITLE}")
            window = windows[0]
            if window.isMinimized:
                window.restore()
                time.sleep(0.1)

            self.analysis_app = Application(backend="uia").connect(title_re=ANALYSIS_TITLE, timeout=10)
            self.window = self.analysis_app.window(title_re=ANALYSIS_TITLE)
            self.window.set_focus()
            logger.info("Analysis软件启动成功")
            return self.window
        except Exception as e:
            error_msg = f"启动Analysis失败: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)
            raise

    def open_xenon_lamp(self):
        logger.info("开始执行打开氙灯操作")
        try:
            logger.info("尝试点击'主控设置'按钮")
            self.click_button("主控设置")
            logger.info("成功点击'主控设置'按钮")

            try:
                logger.info("尝试点击'打开氙灯'按钮")
                self.click_button("打开氙灯")
                logger.info("成功点击'打开氙灯'按钮")
            except Exception as a:
                error_msg = f"打开氙灯失败: {a}"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败
                raise
        except Exception as a:
            error_msg = f"打开主控设置失败: {a}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            raise
        finally:
            try:
                logger.info("尝试关闭主控设置窗口")
                master_control = self.window.child_window(title="MasterControl", control_type="Window")
                master_control.close()
                logger.info("成功关闭主控设置窗口")
            except Exception as a:
                error_msg = f"关闭主控设置窗口失败: {a}"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def close_xenon_lamp(self):
        logger.info("开始执行关闭氙灯操作")
        try:
            logger.info("尝试点击'主控设置'按钮")
            self.click_button("主控设置")
            logger.info("成功点击'主控设置'按钮")

            try:
                logger.info("尝试点击'关闭氙灯'按钮")
                self.click_button("关闭氙灯")
                logger.info("成功点击'关闭氙灯'按钮")
            except Exception as a:
                error_msg = f"关闭氙灯失败: {a}"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败
                raise
        except Exception as a:
            error_msg = f"打开主控设置失败: {a}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            raise
        finally:
            try:
                logger.info("尝试关闭主控设置窗口")
                master_control = self.window.child_window(title="MasterControl", control_type="Window")
                master_control.close()
                logger.info("成功关闭主控设置窗口")
            except Exception as a:
                error_msg = f"关闭主控设置窗口失败: {a}"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def click_button(self, button_name: str = None, auto_id: str = None, timeout: int = 5):
        """
        点击指定名称或自动化ID的按钮
        """
        identifier = auto_id if auto_id else button_name
        logger.info(f"尝试点击按钮 - 标识: {identifier}, 超时时间: {timeout}秒")

        if button_name is None and auto_id is None:
            error_msg = "必须提供 button_name 或 auto_id 参数"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False

        try:
            if auto_id:
                button = self.window.child_window(auto_id=auto_id, control_type="Button")
                logger.debug(f"通过auto_id定位按钮: {auto_id}")
            else:
                button = self.window.child_window(title=button_name, control_type="Button")
                logger.debug(f"通过title定位按钮: {button_name}")

            button.wait("enabled", timeout=timeout)
            logger.debug(f"按钮 '{identifier}' 已就绪")
            button.click_input()
            logger.info(f"成功点击按钮: {identifier}")
            return True

        except TimeoutError as e:
            error_msg = f"按钮 '{identifier}' 在 {timeout} 秒内未找到或不可点击: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False
        except Exception as e:
            error_msg = f"点击按钮 '{identifier}' 时发生意外错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False

    def click_double_button(self, button_name: str, timeout: int = 5):
        """
        双击指定名称的按钮
        """
        logger.info(f"尝试双击按钮 - 名称: {button_name}, 超时时间: {timeout}秒")
        try:
            button = self.window.child_window(title=button_name, control_type="Button")
            logger.debug(f"定位按钮: {button_name}")

            button.wait("enabled", timeout=timeout)
            logger.debug(f"按钮 '{button_name}' 已就绪，准备双击")
            button.double_click_input()
            logger.info(f"成功双击按钮: {button_name}")
        except TimeoutError as e:
            error_msg = f"按钮 '{button_name}' 在 {timeout} 秒内未找到或不可点击: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
        except Exception as e:
            error_msg = f"双击按钮 '{button_name}' 时发生意外错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def select_combo_item(self, auto_id: str, item_text: str, timeout: int = 5):
        """
        在下拉框中选择指定的项
        """
        logger.info(f"尝试在下拉框中选择项 - 下拉框ID: {auto_id}, 选项文本: {item_text}, 超时: {timeout}秒")
        try:
            combo = self.window.child_window(auto_id=auto_id, control_type="ComboBox")
            logger.debug(f"定位下拉框: {auto_id}")
            combo.wait("enabled", timeout=timeout)
            logger.debug(f"下拉框 '{auto_id}' 已就绪")

            combo.click_input()
            logger.debug(f"已展开下拉框 '{auto_id}' 的选项列表")

            target_item = combo.child_window(title=item_text, control_type="ListItem")
            target_item.wait("visible", timeout=timeout)
            logger.debug(f"选项 '{item_text}' 已可见")

            target_item.click_input()
            logger.info(f"成功在下拉框 '{auto_id}' 中选择选项: {item_text}")

        except TimeoutError as e:
            error_msg = f"下拉框 '{auto_id}' 或选项 '{item_text}' 在 {timeout} 秒内未就绪: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
        except Exception as e:
            error_msg = f"选择选项时发生错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def enter_text(self, text: str, auto_id: str = None, control_name: str = None, timeout: int = 5):
        """
        在文本框中输入文本
        """
        identifier = auto_id if auto_id else control_name
        method = "auto_id" if auto_id else "control_name"
        logger.info(f"尝试在文本框中输入文本 - 文本: {text}, 标识: {identifier}, 方式: {method}, 超时: {timeout}秒")

        try:
            if auto_id is None and control_name is None:
                error_msg = "必须提供auto_id或control_name参数"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败
                raise ValueError(error_msg)

            if auto_id:
                edit = self.window.child_window(auto_id=auto_id, control_type="Edit")
                logger.debug(f"通过auto_id定位文本框: {auto_id}")
            else:
                edit = self.window.child_window(title=control_name, control_type="Edit")
                logger.debug(f"通过control_name定位文本框: {control_name}")

            edit.wait("enabled", timeout=timeout)
            logger.debug(f"文本框 '{identifier}' 已就绪，准备输入文本")
            edit.set_text(text)
            logger.info(f"成功在文本框 '{identifier}' 中输入文本: {text}")
        except TimeoutError as e:
            error_msg = f"文本框 '{identifier}' 在 {timeout} 秒内未找到或不可用: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
        except Exception as e:
            error_msg = f"在文本框 '{identifier}' 中输入文本时发生意外错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def get_text(self, auto_id: str = None, control_name: str = None, timeout: int = 5) -> str:
        """
        获取文本框中的值
        """
        identifier = auto_id if auto_id else control_name
        method = "auto_id" if auto_id else "control_name"
        logger.info(f"尝试获取文本框中的值 - 标识: {identifier}, 方式: {method}, 超时: {timeout}秒")

        try:
            if auto_id is None and control_name is None:
                error_msg = "必须提供auto_id或control_name参数"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败
                raise ValueError(error_msg)

            if auto_id:
                edit = self.window.child_window(auto_id=auto_id, control_type="Edit")
                logger.debug(f"通过auto_id定位文本框: {auto_id}")
            else:
                edit = self.window.child_window(title=control_name, control_type="Edit")
                logger.debug(f"通过control_name定位文本框: {control_name}")

            edit.wait("enabled", timeout=timeout)
            logger.debug(f"文本框 '{identifier}' 已就绪，准备获取文本")
            text_value = edit.texts()[0]
            logger.info(f"成功获取文本框 '{identifier}' 中的值: {text_value}")
            return text_value
        except TimeoutError as e:
            error_msg = f"文本框 '{identifier}' 在 {timeout} 秒内未找到或不可用: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
        except Exception as e:
            error_msg = f"获取文本框 '{identifier}' 中的值时发生意外错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败

    def verify_control_exists(self, control_name: str, control_type: str, timeout: int = 5) -> bool:
        """
        验证指定控件是否存在
        """
        logger.info(f"验证控件是否存在 - 控件名称: {control_name}, 控件类型: {control_type}, 超时: {timeout}秒")
        try:
            control = self.window.child_window(title=control_name, control_type=control_type)
            logger.debug(f"尝试定位控件: {control_name} ({control_type})")
            control.wait("exists ready", timeout=timeout)
            logger.info(f"控件 '{control_name}' ({control_type}) 存在")
            return True
        except TimeoutError:
            error_msg = f"控件 '{control_name}' ({control_type}) 在 {timeout} 秒内未找到"
            logger.info(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False
        except Exception as e:
            error_msg = f"验证控件 '{control_name}' 时发生意外错误: {str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False

    def verify_window_appears(self, title, control_type="Window", timeout=5):
        """验证指定窗口是否出现并可见"""
        logger.info(f"验证窗口是否出现 - 窗口标题: {title}, 控件类型: {control_type}, 超时: {timeout}秒")
        target_window = self.window.child_window(title=title, control_type=control_type)
        try:
            logger.debug(f"尝试定位窗口: {title} ({control_type})")
            target_window.wait("exists visible", timeout=timeout)
            logger.info(f"窗口 '{title}' 已出现并可见")
            return target_window
        except Exception as e:
            error_msg = f"窗口 '{title}' 在 {timeout} 秒内未出现或不可见: {str(e)}"
            logger.info(error_msg)
            return None

    def verify_window_appears_and_close(self, title, control_type="Window", timeout=5):
        """验证指定窗口是否出现并可见，出现后立即关闭"""
        logger.info(f"验证窗口是否出现并关闭 - 窗口标题: {title}, 控件类型: {control_type}, 超时: {timeout}秒")
        target_window = self.window.child_window(title=title, control_type=control_type)
        try:
            logger.debug(f"尝试定位窗口: {title} ({control_type})")
            # 等待窗口出现并可见
            target_window.wait("exists visible", timeout=timeout)
            logger.info(f"窗口 '{title}' 已出现并可见，准备关闭")
            # 关闭窗口
            target_window.close()
            logger.info(f"窗口 '{title}' 已成功关闭")
            return True  # 表示窗口出现并关闭成功
        except Exception as e:
            error_msg = f"窗口 '{title}' 处理失败: {str(e)}"
            logger.error(error_msg)
            return False  # 表示处理失败（未出现或关闭失败）

    def verify_window_appears_not_title(self, control_type="Window", timeout=5):
        """验证指定类型的窗口是否出现并可见（不指定标题）"""
        logger.info(f"验证窗口是否出现 - 控件类型: {control_type}, 超时: {timeout}秒")
        target_window = self.window.child_window(control_type=control_type)
        try:
            logger.debug(f"尝试定位类型为 '{control_type}' 的窗口")
            target_window.wait("exists visible", timeout=timeout)
            logger.info(f"类型为 '{control_type}' 的窗口已出现并可见")
            return target_window
        except Exception as e:
            error_msg = f"类型为 '{control_type}' 的窗口在 {timeout} 秒内未出现或不可见: {str(e)}"
            logger.info(error_msg)
            return None

    def get_recipe_window(self, window_title, control_type="Window", timeout=10, retry_interval=0.2):
        """获取指定标题和控件类型的窗口"""
        logger.info(
            f"尝试获取窗口 - 窗口标题: {window_title}, 控件类型: {control_type}, 超时: {timeout}秒, 轮询间隔: {retry_interval}秒")
        recipe_window = self.window.child_window(title=window_title, control_type=control_type)
        try:
            logger.debug(f"开始轮询查找窗口: {window_title}")
            recipe_window.wait('exists visible', timeout=timeout, retry_interval=retry_interval)
            logger.info(f"成功获取窗口: {window_title}")
            return recipe_window
        except Exception as e:
            error_msg = f"窗口查找失败: {str(e)}"
            logger.error(error_msg)
            allure.attach(error_msg, "错误详情", allure.attachment_type.TEXT)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return None

    def capture_window_screenshot(self, name="", timeout=5):
        """
        捕获当前窗口或指定控件的截图
        """
        logger.info(f"尝试捕获截图 - 名称: {name}, 超时: {timeout}秒")
        try:
            logger.debug(f"等待窗口就绪")
            self.window.wait("visible", timeout=timeout)
            logger.debug(f"窗口已就绪，准备截图")

            screenshot = self.window.capture_as_image()
            logger.debug(f"截图成功，准备保存到Allure报告")

            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()

            allure.attach(
                img_byte_arr,
                name=name,
                attachment_type=allure.attachment_type.PNG
            )

            logger.info(f"成功捕获并保存截图: {name}")
            return screenshot
        except Exception as e:
            error_msg = f"截图失败: {str(e)}"
            logger.error(error_msg)
            allure.attach(error_msg, "截图错误", allure.attachment_type.TEXT)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return None

    def verification_error_window_closed (self, error_title=None):
        """验证错误窗口是否存在并关闭"""
        warning_window_title = error_title
        logger.info(f"检查错误窗口是否存在 - 窗口标题: {warning_window_title}")

        warning_window_exists = self.verify_window_appears(warning_window_title, timeout=2)

        if warning_window_exists:
            logger.info(f"发现错误窗口: {warning_window_title}，准备关闭")
            try:
                warning_window_exists.close()
                logger.info(f"成功关闭错误窗口: {warning_window_title}")
            except Exception as e:
                error_msg = f"关闭错误窗口失败: {str(e)}"
                logger.error(error_msg)
                pytest.fail(error_msg)  # 添加pytest.fail标记失败
        else:
            logger.info(f"未发现错误窗口: {warning_window_title}")

        return warning_window_exists

    def is_window_exists(self, title=None, class_name=None, auto_id=None, timeout=10):
        """
        验证独立窗口是否存在
        """
        if not any([title, class_name, auto_id]):
            error_msg = "必须提供title、class_name或auto_id中的至少一个参数"
            logger.warning(error_msg)
            pytest.fail(error_msg)  # 添加pytest.fail标记失败
            return False

        criteria = {}
        if title:
            criteria["title_re"] = title
        if class_name:
            criteria["class_name"] = class_name
        if auto_id:
            criteria["auto_id"] = auto_id

        try:
            window = wait_until_passes(
                timeout=timeout,
                retry_interval=0.5,
                func=lambda: self.desktop.window(**criteria),
                exceptions=TimeoutError
            )
            if window.exists():
                logger.info(f"窗口存在，定位条件: {criteria}")
                return window
            else:
                error_msg = f"超时未找到窗口，定位条件: {criteria}，超时时间: {timeout}秒"
                logger.info(error_msg)
                return False

        except TimeoutError:
            error_msg = f"超时未找到窗口，定位条件: {criteria}，超时时间: {timeout}秒"
            logger.info(error_msg)
            return False
        except Exception as e:
            error_msg = f"检查窗口存在性失败: {str(e)}"
            logger.error(error_msg)
            return False

    @staticmethod
    def ensure_checkbox_checked(target_window, checkbox_title, auto_id=None, timeout=5):
        """
        检查复选框是否勾选，未勾选则勾选
        :param target_window: 目标窗口对象
        :param checkbox_title: 复选框标题
        :param auto_id: 复选框的auto_id属性（可选，用于区分相同标题的复选框）
        :param timeout: 查找控件超时时间
        """
        try:
            # 1. 优先通过auto_id查找
            if auto_id:
                checkbox = target_window.child_window(auto_id=auto_id, control_type="CheckBox")
                checkbox.wait('exists visible', timeout=timeout)
                logger.info(f"通过auto_id「{auto_id}」找到复选框")
            else:
                # 2. 否则通过标题查找
                checkbox = target_window.child_window(title_re=checkbox_title, control_type="CheckBox")
                checkbox.wait('exists visible', timeout=timeout)

            # 检查复选框当前状态
            is_checked = checkbox.get_toggle_state()  # 1=勾选, 0=未勾选
            if not is_checked:
                logger.info(
                    f"复选框「{checkbox_title}」{'(auto_id: ' + auto_id + ')' if auto_id else ''}未勾选，正在自动勾选...")
                checkbox.click()  # 点击勾选
                time.sleep(0.5)  # 等待状态更新

                # 验证是否勾选成功
                if checkbox.get_toggle_state():
                    logger.info(f"复选框「{checkbox_title}」{'(auto_id: ' + auto_id + ')' if auto_id else ''}已成功勾选")
                else:
                    logger.error(f"警告：复选框「{checkbox_title}」{'(auto_id: ' + auto_id + ')' if auto_id else ''}勾选失败")
            else:
                logger.info(f"复选框「{checkbox_title}」{'(auto_id: ' + auto_id + ')' if auto_id else ''}已处于勾选状态")

            return checkbox

        except ElementNotFoundError:
            if auto_id:
                logger.error(f"错误：未找到auto_id为「{auto_id}」或标题为「{checkbox_title}」的复选框")
            else:
                logger.error(f"错误：未找到窗口「{checkbox_title}」或复选框「{checkbox_title}」")
        except Exception as e:
            logger.error(f"操作失败：{str(e)}")

    @staticmethod
    def set_ensure_checkbox_checked(target_window, checkbox_title, need_checked, auto_id=None, timeout=5):
        """
        手动控制复选框状态
        :param target_window: 目标窗口对象
        :param checkbox_title: 复选框标题
        :param need_checked: True=强制勾选，False=强制取消勾选
        :param auto_id: 复选框的自动化ID（可选），如果提供则优先使用
        :param timeout: 超时时间
        """
        try:
            # 优先使用auto_id查找，如果提供了的话
            if auto_id:
                checkbox = target_window.child_window(auto_id=auto_id, control_type="CheckBox")
            else:
                checkbox = target_window.child_window(title=checkbox_title, control_type="CheckBox")

            checkbox.wait('exists visible', timeout=timeout)
            current_checked = checkbox.get_toggle_state()

            if need_checked and not current_checked:
                checkbox.click()
                logger.info(f"已勾选「{checkbox_title}」{'(通过auto_id: ' + auto_id + ')' if auto_id else ''}")
            elif not need_checked and current_checked:
                checkbox.click()
                logger.info(f"已取消勾选「{checkbox_title}」{'(通过auto_id: ' + auto_id + ')' if auto_id else ''}")
            else:
                logger.info(f"「{checkbox_title}」{'(通过auto_id: ' + auto_id + ')' if auto_id else ''}已处于目标状态")
            return checkbox
        except Exception as e:
            logger.error(f"操作「{checkbox_title}」{'(auto_id: ' + auto_id + ')' if auto_id else ''}失败: {str(e)}")
            raise  # 可以根据需要选择是否抛出异常

    def wait_for_control_enabled(
            self,
            control: BaseWrapper,
            timeout: int = 1500,
            check_interval: float = 0.5
    ) -> bool:
        """
        等待控件变为可点击（Enabled）且可见状态
        :param control: pywinauto控件对象
        :param timeout: 最大等待时间（秒）
        :param check_interval: 检查状态的间隔（秒）
        :return: 超时前变为可点击返回True，超时返回False
        """
        start_time = time.time()
        logger.info("开始等待控件可用，超时时间：%d秒", timeout)

        while time.time() - start_time < timeout:
            try:
                # 检查控件是否可用且可见
                if control.is_enabled() and control.is_visible():
                    logger.info("控件已满足enabled+visible条件")
                    return True
            except Exception as e:
                # 控件临时找不到/访问失败，不中断，继续等待
                logger.debug("控件状态检查失败（临时）：%s", str(e)[:50])

            time.sleep(check_interval)

        # 超时返回False
        logger.warning("控件等待超时%d秒，仍不可用", timeout)
        return False

    def find_and_wait_control(
            self,
            main_window,
            control_name: str,
            control_type: str = "Button",
            timeout_seconds: int = 1500,
            check_interval: float = 0.5,
            by_title: bool = True,
            click_after_enabled: bool = False,
            click_type: str = "left"
    ) -> BaseWrapper:
        """
        核心方法：传入main_window + 控件标识 → 定位控件 + 等待可用 + 可选点击
        :param main_window: 外部传入的主窗口对象
        :param control_name: 控件标题/AutomationId（根据by_title决定）
        :param control_type: 控件类型（默认Button，可传Edit/Text等）
        :param timeout: 最大等待时间（秒）
        :param check_interval: 检查状态间隔（秒）
        :param by_title: True=按标题查找，False=按AutomationId查找
        :param click_after_enabled: 控件可用后是否点击（默认False）
        :param click_type: 点击类型（left/right，仅click_after_enabled=True时生效）
        :return: 可用的控件对象
        :raise TimeoutError: 超时未找到可用控件
        :raise TypeError: 非按钮控件尝试点击
        :raise ValueError: 不支持的点击类型/定位控件失败
        """
        # 1. 定位控件（先resolve，确保获取真实控件对象）
        try:
            logger.info("开始定位控件：名称=%s，类型=%s，按标题查找=%s",
                        control_name, control_type, by_title)

            if by_title:
                control_spec = main_window.child_window(
                    title=control_name,
                    control_type=control_type
                )
            else:
                control_spec = main_window.child_window(
                    auto_id=control_name,
                    control_type=control_type
                )
            # 关键修复：resolve获取真实控件对象（避免WindowSpecification对象）
            control = control_spec.wait('exists', timeout=timeout_seconds)
        except Exception as e:
            logger.error("控件定位失败：%s", str(e))
            raise ValueError(f"定位控件失败：{control_name} | 错误：{str(e)}")

        # 2. 等待控件可用
        if self.wait_for_control_enabled(control, timeout_seconds, check_interval):
            # 3. 可选执行点击（修复控件类型判断逻辑）
            if click_after_enabled:
                # 修复：不判断具体Wrapper类型，而是通过控件类型+是否有click方法判断
                if control_type == "Button" and hasattr(control, "click"):
                    if click_type == "left":
                        control.click()
                        logger.info("✅ 控件【%s】可用并执行左键点击", control_name)
                    elif click_type == "right":
                        control.right_click()
                        logger.info("✅ 控件【%s】可用并执行右键点击", control_name)
                    else:
                        raise ValueError(f"不支持的点击类型：{click_type} | 仅支持left/right")
                else:
                    raise TypeError(
                        f"控件【{control_name}】类型为{control_type}，不支持点击操作（仅Button控件且包含click方法可点击）"
                    )

            # 4. 返回可用的控件对象
            return control
        else:
            raise TimeoutError(f"控件【{control_name}】超时{timeout_seconds}秒仍不可用（未满足enabled+visible）")

    def input_filename_and_save(self, main_window, filename):
        """
        极简版：输入文件名并点击保存按钮
        :param main_window: 主窗口对象（如 analysis_app.window()）
        :param filename: 要输入的文件名（如 "test_output.csv"）
        """
        try:
            # 1. 定位文件名输入框并输入
            edit = main_window.child_window(title_re="文件名:", class_name="Edit")
            edit.set_focus()  # 聚焦输入框
            edit.type_keys(filename, with_spaces=True)  # 输入文件名
            logger.info(f"成功输入文件名：{filename}")

            # 2. 定位保存按钮并点击
            save_btn = main_window.child_window(title="保存(S)", control_type="Button")
            save_btn.click_input()  # 点击保存
            logger.info("成功点击保存按钮")

        except ElementNotFoundError as e:
            # 基础保护：捕获元素找不到的异常
            error_msg = f"定位控件失败：{str(e)}"
            logger.error(error_msg)
            pytest.fail(error_msg)  # 中断测试
        except Exception as e:
            # 捕获其他异常
            error_msg = f"保存操作失败：{str(e)}"
            logger.error(error_msg)
            traceback.print_exc()  # 打印报错详情，方便调试
            pytest.fail(error_msg)