import allure
import pyautogui
import io


def attach_screenshot(name: str = "Screenshot"):
    """使用pyautogui捕获屏幕截图并附加到Allure报告"""
    # 捕获全屏
    image = pyautogui.screenshot()

    # 将图像转换为字节流
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # 添加到Allure报告
    allure.attach(img_byte_arr, name=name, attachment_type=allure.attachment_type.PNG)