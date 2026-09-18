# from utils.tools import find_image_and_click, find_image_and_click_with_offset, \
#     safe_paste_filename, escape_pywinauto_chars
# # import time
# # # sleep.time(2)
# # find_image_and_click_with_offset(template_name="load_1.png", y_offset=80, click_type="right",
# #
# #                               img_dir="images/Load_intensity")
# # find_image_and_click(template_name="load.png", click_type="left", img_dir="images/Load_intensity")
#
# find_image_and_click_with_offset(template_name="calc.png", y_offset=500, click_type="right",
#                                  img_dir="images")
# # time.sleep(0.1)
# find_image_and_click(template_name="save.png", click_type="left")


import pytest
import os
import time
import sys
import shutil
import pyautogui
import datetime
pyautogui.FAILSAFE = False  # 禁用安全机制，不会再触发 FailSafeException
from logging_config import logger
from utils.tools import clear_files_in_directory

# ========== 原有配置（全部保留） ==========
EXPORT_RUN_CASES = []
# EXPORT_SKIP_CASES = ["002"]
EXPORT_SKIP_CASES = ["001-057"]
TEST_FILES_WITH_ALLURE = [
    r"D:\Python_Test\Auto_Data_Consisitency\tests\test_data_consistency_v2.py"
]
TEST_FILES_WITHOUT_ALLURE = [
    r"D:\Python_Test\Auto_Data_Consisitency\tests\test_analysis_data_input.py"
]

ALLURE_REPORT_DIR = r"D:\Python_Test\Auto_Data_Consisitency\allure-results"
LOOP_ENABLE = True
LOOP_INTERVAL = 5
MAX_LOOP_TIMES = 15
test_output_dir = r"D:\Esp_DataSet\table_data"

# ========== 【新增】可配置开关 ==========
AUTO_CLEAR_EXPORT_DIR = True       # 每轮开头是否自动清理导出目录（False=保留上一轮残留，方便排查失败数据）
EXPORT_STABLE_CHECK_TIMEOUT = 600  # 等待CSV导出稳定的超时时间（秒），根据你的导出规模调整
EXPORT_STABLE_CHECK_INTERVAL = 3   # 每隔多少秒检查一次文件大小是否稳定
EXPORT_STABLE_REQUIRE_COUNT = 3    # 连续多少次检查文件大小不变=导出完成

# ========== 【新增】存档配置 ==========
ARCHIVE_ROOT_DIR = r"D:\Esp_DataSet\archives"  # 每次循环结果的存档根目录

# ========== expand_case_range：修复"000" bug ==========
def expand_case_range(skip_list):
    """解析跳过用例列表，支持范围（如"001-005"）和单个（如"002"）"""
    expanded_cases = []
    for item in skip_list:
        if "-" in item:
            start_str, end_str = item.split("-")
            start = int(start_str) if start_str.isdigit() else 0
            end = int(end_str) if end_str.isdigit() else 0
            for num in range(start, end + 1):
                expanded_cases.append(f"{num:03d}")
        else:
            num = int(item) if item.isdigit() else 0
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

# ========== 【新增】等待CSV导出完成（替代固定sleep） ==========
def wait_export_done(expected_dir, expected_file_count=None, timeout=600):
    """
    等待CSV导出完成：
    - 若指定expected_file_count：文件数量必须≥此值
    - 文件大小连续N次不变=写入完成
    返回：True=导出完成/False=超时
    """
    if not os.path.isdir(expected_dir):
        logger.error(f"导出目录不存在：{expected_dir}")
        return False

    logger.info(f"开始等待CSV导出完成（目标目录：{expected_dir}，"
                f"期望文件数：{expected_file_count or '不限'}，超时：{timeout}秒）")

    start_time = time.time()
    stable_count = 0
    last_sizes = {}

    while time.time() - start_time < timeout:
        # 1. 列出当前CSV文件
        csv_files = [f for f in os.listdir(expected_dir) if f.endswith(".csv")]

        # 2. 检查文件数量是否达标（如果指定了）
        if expected_file_count and len(csv_files) < expected_file_count:
            logger.info(f"已生成 {len(csv_files)}/{expected_file_count} 个CSV，继续等待...")
            time.sleep(EXPORT_STABLE_CHECK_INTERVAL)
            continue

        # 3. 检查所有文件大小是否连续稳定（不再增长）
        current_sizes = {}
        any_growing = False
        for f in csv_files:
            fpath = os.path.join(expected_dir, f)
            try:
                size = os.path.getsize(fpath)
            except OSError:
                continue
            current_sizes[f] = size
            # 文件从上次检查到现在size变了→还在写
            if f in last_sizes and size != last_sizes[f]:
                any_growing = True

        if any_growing or not last_sizes:
            stable_count = 0
            last_sizes = current_sizes
            logger.info(f"文件还在写入中（已生成 {len(csv_files)} 个），继续等待...")
        else:
            stable_count += 1
            logger.info(f"文件大小稳定中（{stable_count}/{EXPORT_STABLE_REQUIRE_COUNT}）")
            if stable_count >= EXPORT_STABLE_REQUIRE_COUNT:
                elapsed = time.time() - start_time
                logger.info(f"✅ CSV导出完成：共 {len(csv_files)} 个文件，耗时 {elapsed:.1f}秒")
                return True

        last_sizes = current_sizes
        time.sleep(EXPORT_STABLE_CHECK_INTERVAL)

    logger.error(f"❌ CSV导出超时（{timeout}秒），当前仅有 {len(csv_files)} 个CSV文件")
    return False

# ========== 【新增】存档函数 ==========
def archive_round_results(loop_count, export_success, compare_success):
    """
    将本轮执行结果另存为存档，便于后续对比分析：
    - archives/
        └── 第X轮_20260918_192353_导出✓_对比✗/
            ├── export_csv/       ← 本轮导出的所有CSV（失败时为空目录）
            ├── allure-results/   ← 本轮Allure对比报告原始数据（成功时存在）
            └── summary.txt       ← 本轮执行摘要
    """
    # 1. 组装存档目录名
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    export_mark = "✓" if export_success else "✗"
    compare_mark = "✓" if compare_success else "✗"
    archive_name = f"第{loop_count:03d}轮_{now_str}_导出{export_mark}_对比{compare_mark}"
    archive_dir = os.path.join(ARCHIVE_ROOT_DIR, archive_name)

    try:
        os.makedirs(archive_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"创建存档目录失败：{e}")
        return

    # 2. 存档本轮导出的CSV
    export_archive_dir = os.path.join(archive_dir, "export_csv")
    os.makedirs(export_archive_dir, exist_ok=True)
    if export_success and os.path.isdir(test_output_dir):
        for f in os.listdir(test_output_dir):
            if f.endswith(".csv"):
                src = os.path.join(test_output_dir, f)
                dst = os.path.join(export_archive_dir, f)
                try:
                    shutil.copy2(src, dst)
                except Exception as e:
                    logger.warning(f"存档CSV失败 {f}：{e}")
        csv_count = len([f for f in os.listdir(export_archive_dir) if f.endswith(".csv")])
        logger.info(f"📦 已存档本轮导出CSV：{csv_count} 个 → {export_archive_dir}")

    # 3. 存档Allure对比结果（覆盖式复制，避免子目录冲突）
    allure_archive_dir = os.path.join(archive_dir, "allure-results")
    if compare_success and os.path.isdir(ALLURE_REPORT_DIR):
        try:
            shutil.copytree(ALLURE_REPORT_DIR, allure_archive_dir, dirs_exist_ok=True)
            logger.info(f"📦 已存档Allure对比报告 → {allure_archive_dir}")
        except Exception as e:
            logger.warning(f"存档Allure报告失败：{e}")

    # 4. 写执行摘要
    summary_path = os.path.join(archive_dir, "summary.txt")
    summary = f"""===== 第 {loop_count} 轮执行摘要 =====
时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
导出用例：{'✅ 成功' if export_success else '❌ 失败'}
CSV对比：{'✅ 成功（数据一致）' if compare_success else '❌ 失败（有差异/报错）'}
导出CSV数量：{len([f for f in os.listdir(export_archive_dir) if f.endswith(".csv")]) if os.path.isdir(export_archive_dir) else 0}
Allure结果：{'✅ 已存档' if os.path.isdir(allure_archive_dir) else '❌ 无/失败'}
导出目录：{test_output_dir}
Allure原始目录：{ALLURE_REPORT_DIR}
存档目录：{archive_dir}
====================================
"""
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    logger.info(f"📁 第 {loop_count} 轮存档完成 → {archive_dir}")
    print(f"\n📁 第 {loop_count} 轮存档 → {archive_dir}")

# ========== 改造：run_tests_with_allure 返回执行状态 ==========
def run_tests_with_allure(loop_count):
    """执行CSV对比用例，返回 True=全部通过 / False=有失败或收集错误"""
    valid_files = check_test_files(TEST_FILES_WITH_ALLURE)
    if not valid_files:
        logger.warning("没有CSV对比的有效测试文件，跳过")
        return False

    pytest_args = ["-v", "-s"]
    pytest_args.extend(valid_files)
    pytest_args.extend(["--alluredir", ALLURE_REPORT_DIR])
    pytest_args.extend(["-m", "not no_allure_report"])

    os.environ["LOOP_COUNT"] = str(loop_count)

    # 【关键】清空上一轮的allure-results，保证这轮报告纯净
    if os.path.isdir(ALLURE_REPORT_DIR):
        try:
            shutil.rmtree(ALLURE_REPORT_DIR)
        except Exception as e:
            logger.warning(f"清理旧allure-results失败（可能被占用）：{e}")
    os.makedirs(ALLURE_REPORT_DIR, exist_ok=True)

    print(f"\n===== 执行CSV对比 - 第{loop_count}轮 =====")
    print(f"参数：{pytest_args}")
    logger.info(f"第 {loop_count} 轮 CSV对比参数：{pytest_args}")

    try:
        exit_code = pytest.main(pytest_args)
        logger.info(f"pytest退出码={exit_code}")

        # pytest退出码：0=全部通过 / 1=有失败 / 2=收集错误 / 5=没有收集到用例
        if exit_code == 0:
            logger.info(f"✅ 第 {loop_count} 轮 CSV对比全部通过（数据一致）")
            return True
        elif exit_code == 1:
            logger.warning(f"❌ 第 {loop_count} 轮 CSV对比有差异（退出码1）")
            return False  # 有差异也算"执行完成但结果失败"，仍存档
        elif exit_code == 5:
            logger.warning(f"⚠️ 第 {loop_count} 轮 CSV对比未收集到用例（目录为空/参数化返回空列表）")
            return False
        else:
            logger.error(f"❌ 第 {loop_count} 轮 CSV对比异常退出（退出码={exit_code}）")
            return False
    except Exception as e:
        logger.error(f"执行CSV对比时抛异常：{e}")
        return False

# ========== 改造：run_tests_without_allure 返回执行状态 ==========
def run_tests_without_allure():
    """执行导出用例，返回 True=全部通过 / False=有失败"""
    valid_files = check_test_files(TEST_FILES_WITHOUT_ALLURE)
    if not valid_files:
        logger.warning("没有导出的有效测试文件，跳过")
        return False

    pytest_args = ["-v", "-s"]
    pytest_args.extend(valid_files)
    k_filter = build_export_kwarg()
    if k_filter:
        pytest_args.extend(["-k", k_filter])
    pytest_args.extend(["-m", "no_allure_report"])

    print(f"\n===== 执行数据导出 =====")
    print(f"参数：{pytest_args}")
    logger.info(f"导出参数：{pytest_args}")

    try:
        exit_code = pytest.main(pytest_args)
        logger.info(f"pytest退出码={exit_code}")

        if exit_code == 0:
            logger.info("✅ 导出用例全部通过")
            return True
        else:
            logger.error(f"❌ 导出用例有失败/异常（退出码={exit_code}）")
            return False
    except Exception as e:
        logger.error(f"执行导出用例时抛异常：{e}")
        return False

# ========== 主循环 ==========
if __name__ == "__main__":
    print("🚀 开始执行自动化测试循环...")
    print(f"🔄 循环配置：开启={LOOP_ENABLE} | 间隔={LOOP_INTERVAL}秒 | "
          f"最大次数={MAX_LOOP_TIMES if MAX_LOOP_TIMES > 0 else '无限'}")
    print(f"📦 存档根目录：{ARCHIVE_ROOT_DIR}")
    print(f"🧹 自动清理导出目录：{'是' if AUTO_CLEAR_EXPORT_DIR else '否'}")

    # 确保存档根目录存在
    os.makedirs(ARCHIVE_ROOT_DIR, exist_ok=True)

    loop_count = 0
    try:
        while True:
            if not LOOP_ENABLE:
                print("\n📤 循环已关闭，执行单次测试后退出...")
                loop_count = 1

                # 单次执行流程（简化版）
                export_ok = run_tests_without_allure()
                compare_ok = False
                if export_ok and wait_export_done(test_output_dir, timeout=EXPORT_STABLE_CHECK_TIMEOUT):
                    compare_ok = run_tests_with_allure(loop_count)
                archive_round_results(loop_count, export_ok, compare_ok)
                break

            loop_count += 1
            print(f"\n{'='*50}")
            print(f"第 {loop_count} 次循环 - {datetime.datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}")

            # 1. 清理导出目录（可开关）
            if AUTO_CLEAR_EXPORT_DIR:
                try:
                    clear_files_in_directory(test_output_dir)
                    logger.info(f"【轮次{loop_count}】已清理导出目录 {test_output_dir}")
                except Exception as e:
                    logger.error(f"清理导出目录出错：{e}")
            else:
                logger.info(f"【轮次{loop_count}】跳过清理（AUTO_CLEAR_EXPORT_DIR=False）")

            # 2. 执行导出用例，**接住返回值！**
            export_success = run_tests_without_allure()
            if not export_success:
                logger.error(f"【轮次{loop_count}】❌ 导出失败，跳过本轮CSV对比")
                archive_round_results(loop_count, export_success=False, compare_success=False)

                if MAX_LOOP_TIMES > 0 and loop_count >= MAX_LOOP_TIMES:
                    print(f"\n✅ 已达到最大循环次数({MAX_LOOP_TIMES})，退出！")
                    break
                time.sleep(LOOP_INTERVAL)
                continue

            # 3. 等待CSV导出完成（文件数量达标 + 文件大小稳定）
            print("\n⏳ 等待CSV全部写入磁盘...")
            if not wait_export_done(test_output_dir, timeout=EXPORT_STABLE_CHECK_TIMEOUT):
                logger.error(f"【轮次{loop_count}】❌ CSV导出超时/不完整，跳过CSV对比")
                archive_round_results(loop_count, export_success=True, compare_success=False)

                if MAX_LOOP_TIMES > 0 and loop_count >= MAX_LOOP_TIMES:
                    print(f"\n✅ 已达到最大循环次数({MAX_LOOP_TIMES})，退出！")
                    break
                time.sleep(LOOP_INTERVAL)
                continue

            # 4. 执行CSV对比，**接住返回值！**
            compare_success = run_tests_with_allure(loop_count)

            # 5. 【新增】每轮对比结束后存档！
            archive_round_results(loop_count, export_success, compare_success)

            # 6. 判断是否退出循环
            if MAX_LOOP_TIMES > 0 and loop_count >= MAX_LOOP_TIMES:
                print(f"\n✅ 已达到最大循环次数({MAX_LOOP_TIMES})，退出循环！")
                break

            # 7. 等下一轮
            print(f"\n⏳ 等待 {LOOP_INTERVAL} 秒后开始下一轮（Ctrl+C 退出）...")
            time.sleep(LOOP_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n\n🛑 用户手动中断（Ctrl+C），共执行了 {loop_count} 次循环")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"循环执行出错：{e}")
        sys.exit(1)