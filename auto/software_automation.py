# # software_automation.py
# import pyautogui
# import pytest
# from pywinauto import Application, Desktop
# from pywinauto.mouse import right_click, double_click, click
# from pywinauto.keyboard import send_keys
# import time
# import logging
# import os  # 新增：路径校验
# import sys  # 新增：系统相关操作
#
# # ===================== 修复1：内置日志配置（替代自定义logging_config）=====================
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.StreamHandler(sys.stdout),  # 输出到控制台
#         logging.FileHandler("software_auto.log", encoding="utf-8")  # 输出到日志文件（可选）
#     ]
# )
# logger = logging.getLogger(__name__)
#
#
# class SoftwareAutoHandler:
#     def click_button(self, button_name: str = None, auto_id: str = None, timeout: int = 5):
#         """
#         点击指定名称或自动化ID的按钮
#         """
#         identifier = auto_id if auto_id else button_name
#         logger.info(f"尝试点击按钮 - 标识: {identifier}, 超时时间: {timeout}秒")
#
#         if button_name is None and auto_id is None:
#             error_msg = "必须提供 button_name 或 auto_id 参数"
#             logger.error(error_msg)
#             pytest.fail(error_msg)  # 添加pytest.fail标记失败
#             return False
#
#         try:
#             if auto_id:
#                 button = self.window.child_window(auto_id=auto_id, control_type="Button")
#                 logger.debug(f"通过auto_id定位按钮: {auto_id}")
#             else:
#                 button = self.window.child_window(title=button_name, control_type="Button")
#                 logger.debug(f"通过title定位按钮: {button_name}")
#
#             button.wait("enabled", timeout=timeout)
#             logger.debug(f"按钮 '{identifier}' 已就绪")
#             button.click_input()
#             logger.info(f"成功点击按钮: {identifier}")
#             return True
#
#         except TimeoutError as e:
#             error_msg = f"按钮 '{identifier}' 在 {timeout} 秒内未找到或不可点击: {str(e)}"
#             logger.error(error_msg)
#             pytest.fail(error_msg)  # 添加pytest.fail标记失败
#             return False
#         except Exception as e:
#             error_msg = f"点击按钮 '{identifier}' 时发生意外错误: {str(e)}"
#             logger.error(error_msg)
#             pytest.fail(error_msg)  # 添加pytest.fail标记失败
#             return False
#     def right_click_at_position(x: int, y: int, delay: float = 1.0):
#         """
#         将鼠标移动到指定坐标并执行右键单击操作
#
#         Args:
#             x: 目标横坐标
#             y: 目标纵坐标
#             delay: 移动到目标位置后的延迟时间（秒），避免操作过快导致失效
#         """
#         try:
#             # 1. 移动鼠标到指定坐标
#             pyautogui.moveTo(x, y, duration=0.5)  # duration是移动耗时（秒），使移动更平滑
#             # 2. 延迟片刻，确保鼠标到位
#             time.sleep(delay)
#             # 3. 执行右键单击
#             pyautogui.rightClick()
#             print(f"已在坐标({x}, {y})执行右键操作")
#
#         except Exception as e:
#             print(f"操作失败：{str(e)}")
#
#     def wait_control_exists(self, control_locator, timeout=DEFAULT_CONTROL_TIMEOUT):
#         """等待控件出现"""
#         try:
#             if not self.main_window:
#                 logger.error("【控件操作失败】主窗口未初始化")
#                 return None
#             control = self.main_window.child_window(**control_locator)
#             control.wait('exists', timeout=timeout)
#             logger.info(f"控件已找到：{control_locator}")
#             return control
#         except Exception as e:
#             logger.error(f"等待控件失败 {control_locator}：{str(e)}")
#             return None
#
#     def click_control(self, control_locator, timeout=DEFAULT_CONTROL_TIMEOUT):
#         """单击控件"""
#         control = self.wait_control_exists(control_locator, timeout)
#         if control:
#             try:
#                 control.click()
#                 logger.info(f"单击控件成功：{control_locator}")
#                 return True
#             except Exception as e:
#                 logger.error(f"单击控件失败 {control_locator}：{str(e)}")
#                 return False
#         return False
#
#     def double_click_control(self, control_locator, timeout=DEFAULT_CONTROL_TIMEOUT):
#         """双击控件"""
#         control = self.wait_control_exists(control_locator, timeout)
#         if control:
#             try:
#                 double_click(control.rectangle().mid_point())
#                 logger.info(f"双击控件成功：{control_locator}")
#                 return True
#             except Exception as e:
#                 logger.error(f"双击控件失败 {control_locator}：{str(e)}")
#                 return False
#         return False
#
#     def right_click_control(self, control_locator, timeout=DEFAULT_CONTROL_TIMEOUT):
#         """右键单击控件"""
#         control = self.wait_control_exists(control_locator, timeout)
#         if control:
#             try:
#                 right_click(control.rectangle().mid_point())
#                 logger.info(f"右键单击控件成功：{control_locator}")
#                 return True
#             except Exception as e:
#                 logger.error(f"右键单击控件失败 {control_locator}：{str(e)}")
#                 return False
#         return False
#
#     def input_text_to_control(self, control_locator, text, timeout=DEFAULT_CONTROL_TIMEOUT):
#         """向控件输入文本"""
#         control = self.wait_control_exists(control_locator, timeout)
#         if control:
#             try:
#                 control.click()  # 先激活控件
#                 control.type_keys(text)  # 替代send_keys，更稳定
#                 logger.info(f"向控件输入文本成功 {control_locator}：{text}")
#                 return True
#             except Exception as e:
#                 logger.error(f"向控件输入文本失败 {control_locator}：{str(e)}")
#                 return False
#         return False
#
#     def click_coordinate(self, x, y):
#         """按坐标单击"""
#         try:
#             click(coords=(x, y))
#             logger.info(f"单击坐标成功：({x}, {y})")
#             return True
#         except Exception as e:
#             logger.error(f"单击坐标失败 ({x}, {y})：{str(e)}")
#             return False