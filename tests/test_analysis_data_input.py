import time
import allure
import pytest
from path_config.file_name_config import SAVE_FILE_NAMES
from path_config.path import Test_Import_Address_001, Test_save_Address_path
from utils.tools import find_image_and_click, find_image_and_click_with_offset, \
    safe_paste_filename, escape_pywinauto_chars

# ========== 自动生成参数化数据 ==========
test_cases = [(num, name) for num, name in SAVE_FILE_NAMES.items()]

@pytest.mark.no_allure_report
class Test_Analysis_Data_Input:
    @pytest.mark.parametrize("case_num, file_name", test_cases)
    def test_case(self, app, main_window, pywinauto_base, case_num, file_name):
        """通用用例模板，自动适配所有配置的文件名"""
        # 给用例添加可读的标识（关键：让-k能匹配到）
        allure.dynamic.title(f"测试用例_{case_num}_{file_name}")

        with allure.step(f"【{case_num}】1.移除工程"):
            main_window.wait("ready", timeout=120)
            find_image_and_click("project.png", click_type="right")
            time.sleep(0.1)
            find_image_and_click("remove.png", click_type="left")
            dialog = app.window(control_type="Window", title="确认删除", class_name="QMessageBox")
            yes_btn = dialog.child_window(title="Yes", control_type="Button")
            yes_btn.click()

        with allure.step(f"【{case_num}】2.导入工程"):
            main_window.wait("ready", timeout=120)
            time.sleep(0.01)
            find_image_and_click_with_offset(template_name="manager.png", y_offset=200, click_type="right",
                                             img_dir="images")
            time.sleep(0.01)
            find_image_and_click(template_name="import.png", click_type="left")
            time.sleep(0.1)

            # 定位文件对话框
            dialog = main_window.child_window(class_name="#32770", control_type="Window")
            dialog.wait('visible', timeout=8)

            # 跳转到导入目录
            dialog.type_keys("^l")
            dialog.type_keys("^a{BACKSPACE}")
            dialog.type_keys(Test_Import_Address_001, with_spaces=True)
            dialog.type_keys("{ENTER}")

            # 输入文件名（从字典中获取，自动转义）
            dialog.type_keys("%n")
            time.sleep(0.1)
            full_file_name = f"{file_name}.json"
            dialog.type_keys("^a{BACKSPACE}")
            escaped_name = escape_pywinauto_chars(full_file_name)
            dialog.type_keys(escaped_name, with_spaces=True)
            time.sleep(0.2)
            # 点击打开
            open_btns = dialog.child_window(title="打开(O)", control_type="Button")
            open_btns.wait('enabled', timeout=3)
            open_btns.click()

        with allure.step(f"【{case_num}】3.加载光强文件"):
            main_window.wait("ready", timeout=120)
            find_image_and_click_with_offset(template_name="load_1.png", y_offset=155, click_type="right",
                                             img_dir="images/Load_intensity")
            find_image_and_click(template_name="load.png", click_type="left", img_dir="images/Load_intensity")

        with allure.step(f"【{case_num}】4.光强加载时间等待"):
            pywinauto_base.find_and_wait_control(main_window=main_window, control_name="计算", control_type="Button",
                                                 click_after_enabled=False)

        with allure.step(f"【{case_num}】5.点击计算"):
            pywinauto_base.find_and_wait_control(main_window=main_window, control_name="计算", control_type="Button",
                                                 click_after_enabled=True)

        with allure.step(f"【{case_num}】6.设置数据集计算等待时间"):
            pywinauto_base.find_and_wait_control(main_window=main_window, control_name="计算", control_type="Button",
                                                 click_after_enabled=False)

        with allure.step(f"【{case_num}】7.导出表格至指定目录"):
            find_image_and_click_with_offset(template_name="calc.png", y_offset=800, click_type="right",
                                             img_dir="images")
            time.sleep(0.1)
            find_image_and_click(template_name="save.png", click_type="left")

            # 定位保存对话框
            dialog = main_window.child_window(class_name="#32770", control_type="Window")
            dialog.wait('visible', timeout=8)

            # 跳转到保存目录
            dialog.type_keys("^l")
            dialog.type_keys("^a{BACKSPACE}")
            dialog.type_keys(Test_save_Address_path, with_spaces=True)
            dialog.type_keys("{ENTER}")

            # 输入保存文件名
            file_name_edit = dialog.child_window(control_type="Edit", title="文件名:")
            file_name_edit.wait('enabled', timeout=2)
            file_name_edit.set_focus()
            full_file_name = f"{file_name}"
            safe_paste_filename(full_file_name, file_name_edit)

            # 点击保存
            save_btn = dialog.child_window(title="保存(S)", control_type="Button")
            save_btn.wait('enabled', timeout=3)
            save_btn.click()


if __name__ == "__main__":
    pytest.main(["-v", __file__])