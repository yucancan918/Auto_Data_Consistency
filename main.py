import pytest
import os
import time
import sys
import shutil  # 新增：如果需要清理allure目录的话

from logging_config import logger
from utils.tools import clear_files_in_directory

# ========== 原有配置保持不变 ==========
EXPORT_RUN_CASES = []
EXPORT_SKIP_CASES = ["009-017", "021","022", "002"]
TEST_FILES_WITH_ALLURE = [
    r"D:\Python_Test\Auto_Data_Consisitency\tests\test_data_consistency_v2.py"
]
TEST_FILES_WITHOUT_ALLURE = [
    r"D:\Python_Test\Auto_Data_Consisitency\tests\test_analysis_data_input.py"
]
ALLURE_REPORT_DIR = r"D:\Python_Test\Auto_Data_Consisitency\allure-results"
LOOP_ENABLE = True
LOOP_INTERVAL = 5
MAX_LOOP_TIMES = 1
test_output_dir = r"D:\Esp_DataSet\table_data"


# ========== 原有函数保持不变（expand_case_range/build_export_kwarg/check_test_files） ==========
def expand_case_range(skip_list):
    expanded_cases = []
    for item in skip_list:
        if "-" in item:
            start_str, end_str = item.split("-")
            start = int(start_str.lstrip("0")) if start_str.lstrip("0") else 0
            end = int(end_str.lstrip("0")) if end_str.lstrip("0") else 0
            for num in range(start, end + 1):
                expanded_cases.append(f"{num:03d}")
        else:
            num = int(item.lstrip("0")) if item.lstrip("0") else 0
            expanded_cases.append(f"{num:03d}")
    return expanded_cases


def build_export_kwarg():
    match_parts = []
    if EXPORT_RUN_CASES:
        run_expr = " or ".join(EXPORT_RUN_CASES)
        match_parts.append(run_expr)
    else:
        match_parts.append("test_case")

    if EXPORT_SKIP_CASES:
        expanded_skips = expand_case_range(EXPORT_SKIP_CASES)
        skip_expr = " and ".join([f"not {num}" for num in expanded_skips])
        match_parts.append(skip_expr)

    return " and ".join(match_parts) if match_parts else ""


def check_test_files(file_paths):
    valid_paths = []
    for file_path in file_paths:
        if os.path.exists(file_path):
            print(f"✅ 测试文件路径正确：{file_path}")
            valid_paths.append(file_path)
        else:
            print(f"❌ 错误：测试文件不存在！路径：{file_path}")
    return valid_paths


# ========== 改造run_tests_with_allure：传入循环次数环境变量 ==========
def run_tests_with_allure(loop_count):
    """执行需要生成Allure报告的用例（传入循环次数）"""
    valid_files = check_test_files(TEST_FILES_WITH_ALLURE)
    if not valid_files:
        print("⚠️ 没有需要生成Allure报告的有效测试文件，跳过该部分执行")
        return

    pytest_args = ["-v", "-s"]
    pytest_args.extend(valid_files)
    pytest_args.extend(["--alluredir", ALLURE_REPORT_DIR])
    pytest_args.extend(["-m", "not no_allure_report"])

    # 关键：设置环境变量，传递当前循环次数给测试用例
    os.environ["LOOP_COUNT"] = str(loop_count)

    print(f"\n===== 执行需要Allure报告的测试（CSV对比）- 第{loop_count}轮 =====\n参数：{pytest_args}")
    try:
        pytest.main(pytest_args)
    except Exception as e:
        print(f"❌ 执行带Allure报告的测试出错：{str(e)}")


# ========== 原有run_tests_without_allure保持不变 ==========
def run_tests_without_allure():
    valid_files = check_test_files(TEST_FILES_WITHOUT_ALLURE)
    if not valid_files:
        print("⚠️ 没有不需要生成Allure报告的有效测试文件，跳过该部分执行")
        return

    pytest_args = ["-v", "-s"]
    pytest_args.extend(valid_files)
    k_filter = build_export_kwarg()
    if k_filter:
        pytest_args.extend(["-k", k_filter])
    pytest_args.extend(["-m", "no_allure_report"])

    print(f"\n===== 执行不需要Allure报告的测试（数据导出） =====\n参数：{pytest_args}")
    try:
        pytest.main(pytest_args)
    except Exception as e:
        print(f"❌ 执行不带Allure报告的测试出错：{str(e)}")


# ========== 改造主循环：传入循环次数 ==========
if __name__ == "__main__":
    print("🚀 开始执行自动化测试循环...")
    print(
        f"🔄 循环配置：开启={LOOP_ENABLE} | 间隔={LOOP_INTERVAL}秒 | 最大次数={MAX_LOOP_TIMES if MAX_LOOP_TIMES > 0 else '无限'}")

    loop_count = 0
    try:
        while True:
            if not LOOP_ENABLE:
                print("\n📤 循环已关闭，执行单次测试后退出...")
                # 单次执行时循环次数设为1
                run_tests_without_allure()
                run_tests_with_allure(1)
                break

            loop_count += 1
            print(f"\n========== 第 {loop_count} 次循环 ==========")

            # 1. 清理导出目录
            try:
                clear_files_in_directory(test_output_dir)
                logger.info(f"预处理完成：清理 {test_output_dir} 下文件")
            except Exception as e:
                logger.error(f"清理警告：{test_output_dir} 出错 - {str(e)}")
            logger.info(f"第 {loop_count} 次循环清理table_data完成")

            # 2. 执行导出用例
            run_tests_without_allure()

            # 3. 等待导出完成
            print("\n⏳ 等待数据导出完成，准备执行CSV对比...")
            time.sleep(2)

            # 4. 执行对比用例（传入当前循环次数）
            run_tests_with_allure(loop_count)

            if MAX_LOOP_TIMES > 0 and loop_count >= MAX_LOOP_TIMES:
                print(f"\n✅ 已达到最大循环次数({MAX_LOOP_TIMES})，退出循环！")
                break

            print(f"\n⏳ 等待 {LOOP_INTERVAL} 秒后开始下一次循环（按 Ctrl+C 可强制退出）...")
            time.sleep(LOOP_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n🛑 用户手动中断（Ctrl+C），共执行了 {loop_count} 次循环！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 循环执行出错：{str(e)}")
        sys.exit(1)






# import pytest
# import os
# import time
# import sys
#
# from logging_config import logger
# from utils.tools import clear_files_in_directory
#
# # ========== 配置项 ==========
# # 仅给导出用例用的过滤规则
# EXPORT_RUN_CASES = ["007"]  # 重命名，明确用途
# EXPORT_SKIP_CASES = ["011-017", "022", "002"]
#
# # 拆分测试文件：需要Allure报告 vs 不需要Allure报告
# TEST_FILES_WITH_ALLURE = [
#     r"D:\Python_Test\Auto_Data_Consisitency\tests\test_data_consistency.py"  # 需要报告的文件（对比）
# ]
# TEST_FILES_WITHOUT_ALLURE = [
#     r"D:\Python_Test\Auto_Data_Consisitency\tests\test_analysis_data_input.py"  # 不需要报告的文件（导出）
# ]
#
# # Allure报告保存路径（按需修改）
# ALLURE_REPORT_DIR = r"D:\Python_Test\Auto_Data_Consisitency\allure-results"
#
# # 循环配置
# LOOP_ENABLE = True
# LOOP_INTERVAL = 5
# MAX_LOOP_TIMES = 1
#
#
# def expand_case_range(skip_list):
#     """解析区间表达式，展开为具体的用例编号列表"""
#     expanded_cases = []
#     for item in skip_list:
#         if "-" in item:
#             start_str, end_str = item.split("-")
#             start = int(start_str.lstrip("0")) if start_str.lstrip("0") else 0
#             end = int(end_str.lstrip("0")) if end_str.lstrip("0") else 0
#             for num in range(start, end + 1):
#                 expanded_cases.append(f"{num:03d}")
#         else:
#             num = int(item.lstrip("0")) if item.lstrip("0") else 0
#             expanded_cases.append(f"{num:03d}")
#     return expanded_cases
#
#
# def build_export_kwarg():
#     """仅为导出用例构建过滤表达式"""
#     match_parts = []
#     if EXPORT_RUN_CASES:
#         run_expr = " or ".join(EXPORT_RUN_CASES)
#         match_parts.append(run_expr)
#     else:
#         match_parts.append("test_case")
#
#     if EXPORT_SKIP_CASES:
#         expanded_skips = expand_case_range(EXPORT_SKIP_CASES)
#         skip_expr = " and ".join([f"not {num}" for num in expanded_skips])
#         match_parts.append(skip_expr)
#
#     return " and ".join(match_parts) if match_parts else ""
#
#
# def check_test_files(file_paths):
#     """检查测试文件是否存在"""
#     valid_paths = []
#     for file_path in file_paths:
#         if os.path.exists(file_path):
#             print(f"✅ 测试文件路径正确：{file_path}")
#             valid_paths.append(file_path)
#         else:
#             print(f"❌ 错误：测试文件不存在！路径：{file_path}")
#     return valid_paths
#
#
# def run_tests_with_allure():
#     """执行需要生成Allure报告的用例（对比用例，无编号过滤）"""
#     valid_files = check_test_files(TEST_FILES_WITH_ALLURE)
#     if not valid_files:
#         print("⚠️ 没有需要生成Allure报告的有效测试文件，跳过该部分执行")
#         return
#
#     pytest_args = ["-v", "-s"]
#     pytest_args.extend(valid_files)
#
#     # 添加Allure参数（生成报告）
#     pytest_args.extend(["--alluredir", ALLURE_REPORT_DIR])
#
#     # 对比用例：取消编号过滤，仅排除no_allure_report标记
#     pytest_args.extend(["-m", "not no_allure_report"])
#
#     print(f"\n===== 执行需要Allure报告的测试（CSV对比） =====\n参数：{pytest_args}")
#     try:
#         pytest.main(pytest_args)
#     except Exception as e:
#         print(f"❌ 执行带Allure报告的测试出错：{str(e)}")
#
#
# def run_tests_without_allure():
#     """执行不需要生成Allure报告的用例（导出用例，用编号过滤）"""
#     valid_files = check_test_files(TEST_FILES_WITHOUT_ALLURE)
#     if not valid_files:
#         print("⚠️ 没有不需要生成Allure报告的有效测试文件，跳过该部分执行")
#         return
#
#     pytest_args = ["-v", "-s"]
#     pytest_args.extend(valid_files)
#
#     # 导出用例：用编号过滤 + 只执行no_allure_report标记的用例
#     k_filter = build_export_kwarg()
#     if k_filter:
#         pytest_args.extend(["-k", k_filter])
#     pytest_args.extend(["-m", "no_allure_report"])
#
#     print(f"\n===== 执行不需要Allure报告的测试（数据导出） =====\n参数：{pytest_args}")
#     try:
#         pytest.main(pytest_args)
#     except Exception as e:
#         print(f"❌ 执行不带Allure报告的测试出错：{str(e)}")
#
# test_output_dir = r"D:\Esp_DataSet\table_data"
# if __name__ == "__main__":
#     print("🚀 开始执行自动化测试循环...")
#     print(
#         f"🔄 循环配置：开启={LOOP_ENABLE} | 间隔={LOOP_INTERVAL}秒 | 最大次数={MAX_LOOP_TIMES if MAX_LOOP_TIMES > 0 else '无限'}")
#
#     loop_count = 0
#     try:
#         while True:
#             if not LOOP_ENABLE:
#                 print("\n📤 循环已关闭，执行单次测试后退出...")
#                 run_tests_without_allure()
#                 run_tests_with_allure()
#                 break
#             loop_count += 1
#             print(f"\n========== 第 {loop_count} 次循环 ==========")
#             # 2. 清理其他目录
#             try:
#                 clear_files_in_directory(test_output_dir)
#                 logger.info(f"预处理完成：清理 {test_output_dir} 下文件")
#             except Exception as e:
#                 logger.error(f"清理警告：{test_output_dir} 出错 - {str(e)}")
#             logger.info("第 {loop_count} 次循环清理table_data完成")
#             # 第一步：先执行不需要Allure报告的用例（数据导出，不加Allure参数）
#             run_tests_without_allure()
#
#             # 新增：等待2秒，确保导出文件完全写入磁盘
#             print("\n⏳ 等待数据导出完成，准备执行CSV对比...")
#             time.sleep(2)
#
#             # 第二步：后执行需要Allure报告的用例（数据对比，加Allure参数）
#             run_tests_with_allure()
#
#             if MAX_LOOP_TIMES > 0 and loop_count >= MAX_LOOP_TIMES:
#                 print(f"\n✅ 已达到最大循环次数({MAX_LOOP_TIMES})，退出循环！")
#                 break
#
#             print(f"\n⏳ 等待 {LOOP_INTERVAL} 秒后开始下一次循环（按 Ctrl+C 可强制退出）...")
#             time.sleep(LOOP_INTERVAL)
#
#     except KeyboardInterrupt:
#         print(f"\n\n🛑 用户手动中断（Ctrl+C），共执行了 {loop_count} 次循环！")
#         sys.exit(0)
#     except Exception as e:
#         print(f"\n❌ 循环执行出错：{str(e)}")
#         sys.exit(1)