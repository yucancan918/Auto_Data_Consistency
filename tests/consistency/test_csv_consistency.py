import os
import csv
import pytest
import allure
import re

from tests.logging_config import logger

BASELINE = r"D:\desktop\CS"
ANALYSIS_FOLDER = r"D:\Esp_DataSet\table_data"

BASE_TARGET_FIELDS = {"平均光强", "最大光强"}
THICKNESS_FIELD_PATTERN = re.compile(r"厚度#\d+\(A\)")
THICKNESS_ERROR_THRESHOLD = 0.00010001

BASELINE_NAME = "EpdAnalysis_4.1.1.11"
ANALYSIS_NAME = "EpdAnalysis_4.2.2.9"


def natural_sort_key(s):
    """生成自然排序的key（提取文件名中的数字，用于id1、id2、id3...排序）"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    return [convert(c) for c in re.split('([0-9]+)', s)]


def get_matching_csvs():
    """获取两个文件夹中名称相同的CSV文件，并按自然顺序排序"""
    baseline_files = {f for f in os.listdir(BASELINE) if f.endswith(".csv")}
    analysis_files = {f for f in os.listdir(ANALYSIS_FOLDER) if f.endswith(".csv")}

    matching_files = list(baseline_files & analysis_files)
    matching_files.sort(key=natural_sort_key)
    return matching_files


def read_csv_by_rows(file_path):
    """读取CSV，返回行数据、基础字段索引、厚度字段索引、编码、厚度最后有效行索引"""
    for encoding in ["utf-8-sig", "gbk", "gb2312"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                rows = [row for row in reader]

            if not rows:
                return rows, {}, {}, encoding, 0

            header = rows[0]

            base_indices = {
                field: idx
                for idx, field in enumerate(header)
                if field in BASE_TARGET_FIELDS
            }

            thickness_indices = {}
            for idx, field in enumerate(header):
                if THICKNESS_FIELD_PATTERN.match(field):
                    thickness_indices[field] = idx

            thickness_last_rows = []
            for thick_field, thick_idx in thickness_indices.items():
                last_thick_row_idx = 0
                for row_idx in range(1, len(rows)):
                    row = rows[row_idx]
                    if thick_idx < len(row) and row[thick_idx].strip():
                        last_thick_row_idx = row_idx

                thickness_last_rows.append(last_thick_row_idx)
                logger.debug(
                    f"{file_path} 中 {thick_field} 的最后有效行索引：{last_thick_row_idx}"
                )

            overall_last_row = min(thickness_last_rows) if thickness_last_rows else 0

            return rows, base_indices, thickness_indices, encoding, overall_last_row

        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法读取文件 {file_path}，编码不支持")


def compare_by_row(
    analysis_rows,
    analysis_base_indices,
    analysis_thickness_indices,
    analysis_last_row,
    baseline_rows,
    baseline_base_indices,
    baseline_thickness_indices,
    baseline_last_row,
    csv_name,
):
    """按行号对比目标字段列。光强0容忍，厚度允许≤0.00010001误差"""
    differences = []

    common_thickness_fields = (
        set(analysis_thickness_indices.keys()) & set(baseline_thickness_indices.keys())
    )

    missing_analysis_base = BASE_TARGET_FIELDS - analysis_base_indices.keys()
    missing_baseline_base = BASE_TARGET_FIELDS - baseline_base_indices.keys()

    if missing_analysis_base:
        msg = f"分析文件({ANALYSIS_NAME})缺少基础字段：{missing_analysis_base}"
        differences.append(msg)
        logger.error(f"{csv_name}：{msg}")

    if missing_baseline_base:
        msg = f"基准文件({BASELINE_NAME})缺少基础字段：{missing_baseline_base}"
        differences.append(msg)
        logger.error(f"{csv_name}：{msg}")

    if not common_thickness_fields:
        msg = "两个文件无共同的厚度#N(A)字段，仅对比平均/最大光强"
        differences.append(msg)
        logger.warning(f"{csv_name}：{msg}")
    else:
        analysis_only_thickness = (
            set(analysis_thickness_indices.keys()) - common_thickness_fields
        )
        baseline_only_thickness = (
            set(baseline_thickness_indices.keys()) - common_thickness_fields
        )

        if analysis_only_thickness:
            logger.warning(
                f"{csv_name}：分析文件({ANALYSIS_NAME})独有厚度字段：{analysis_only_thickness}（未参与对比）"
            )

        if baseline_only_thickness:
            logger.warning(
                f"{csv_name}：基准文件({BASELINE_NAME})独有厚度字段：{baseline_only_thickness}（未参与对比）"
            )

    max_row_idx = min(analysis_last_row, baseline_last_row)

    if max_row_idx == 0:
        if common_thickness_fields:
            msg = "所有厚度#N(A)字段无有效行，无法对比厚度相关数据"
            differences.append(msg)
            logger.error(f"{csv_name}：{msg}")

        max_row_idx = min(len(analysis_rows) - 1, len(baseline_rows) - 1)

    if max_row_idx < 1:
        msg = "无有效数据行可对比"
        differences.append(msg)
        logger.error(f"{csv_name}：{msg}")
        return differences

    for row_idx in range(1, max_row_idx + 1):
        row_num = row_idx + 1

        analysis_row = analysis_rows[row_idx] if row_idx < len(analysis_rows) else []
        baseline_row = baseline_rows[row_idx] if row_idx < len(baseline_rows) else []

        # 对比基础字段：平均光强、最大光强，0容忍
        for field in BASE_TARGET_FIELDS:
            if field not in analysis_base_indices or field not in baseline_base_indices:
                continue

            analysis_col_idx = analysis_base_indices[field]
            baseline_col_idx = baseline_base_indices[field]

            analysis_val = (
                analysis_row[analysis_col_idx].strip()
                if analysis_col_idx < len(analysis_row)
                else ""
            )
            baseline_val = (
                baseline_row[baseline_col_idx].strip()
                if baseline_col_idx < len(baseline_row)
                else ""
            )

            is_same = False

            try:
                analysis_float = float(analysis_val)
                baseline_float = float(baseline_val)
                is_same = analysis_float == baseline_float
            except (ValueError, TypeError):
                is_same = analysis_val == baseline_val

            if not is_same:
                try:
                    analysis_float = float(analysis_val)
                    baseline_float = float(baseline_val)
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（光强0容忍，数值不相等）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )
                except (ValueError, TypeError):
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（非数值/空值）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )

                differences.append(msg)
                logger.error(f"{csv_name}：{msg}")

        # 对比厚度字段：允许误差 ≤ 0.00010001
        for field in common_thickness_fields:
            analysis_col_idx = analysis_thickness_indices[field]
            baseline_col_idx = baseline_thickness_indices[field]

            analysis_val = (
                analysis_row[analysis_col_idx].strip()
                if analysis_col_idx < len(analysis_row)
                else ""
            )
            baseline_val = (
                baseline_row[baseline_col_idx].strip()
                if baseline_col_idx < len(baseline_row)
                else ""
            )

            is_same = False
            error = None

            try:
                analysis_float = float(analysis_val)
                baseline_float = float(baseline_val)
                error = abs(analysis_float - baseline_float)
                is_same = error <= THICKNESS_ERROR_THRESHOLD
            except (ValueError, TypeError):
                is_same = analysis_val == baseline_val

            if not is_same:
                if error is not None:
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（误差{error:.8f} > {THICKNESS_ERROR_THRESHOLD}）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )
                else:
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（非数值/空值）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )

                differences.append(msg)
                logger.error(f"{csv_name}：{msg}")

    return differences


@pytest.mark.parametrize("csv_name", get_matching_csvs())
def test_row_by_row_comparison(csv_name):
    """按行号对比目标字段列，支持多厚度#N(A)字段对比"""
    analysis_file = os.path.join(ANALYSIS_FOLDER, csv_name)
    baseline_file = os.path.join(BASELINE, csv_name)

    allure.dynamic.title(f"对比CSV：{csv_name}")
    allure.dynamic.description(
        f"分析文件({ANALYSIS_NAME})：{analysis_file}\n基准文件({BASELINE_NAME})：{baseline_file}"
    )

    with allure.step("读取CSV完整行数据及厚度字段信息"):
        (
            analysis_rows,
            analysis_base_indices,
            analysis_thickness_indices,
            analysis_encoding,
            analysis_last_row,
        ) = read_csv_by_rows(analysis_file)

        (
            baseline_rows,
            baseline_base_indices,
            baseline_thickness_indices,
            baseline_encoding,
            baseline_last_row,
        ) = read_csv_by_rows(baseline_file)

        analysis_thickness_fields = list(analysis_thickness_indices.keys())
        baseline_thickness_fields = list(baseline_thickness_indices.keys())
        common_thickness_fields = list(
            set(analysis_thickness_fields) & set(baseline_thickness_fields)
        )

        attach_info = (
            f"=== {ANALYSIS_NAME} ===\n"
            f"编码：{analysis_encoding}\n"
            f"基础字段：{list(analysis_base_indices.keys())}\n"
            f"厚度字段：{analysis_thickness_fields}\n"
            f"厚度最后有效行索引：{analysis_last_row}\n\n"
            f"=== {BASELINE_NAME} ===\n"
            f"编码：{baseline_encoding}\n"
            f"基础字段：{list(baseline_base_indices.keys())}\n"
            f"厚度字段：{baseline_thickness_fields}\n"
            f"厚度最后有效行索引：{baseline_last_row}\n\n"
            f"=== 对比规则 ===\n"
            f"共同厚度字段：{common_thickness_fields}\n"
            f"厚度误差阈值：≤{THICKNESS_ERROR_THRESHOLD}\n"
            f"对比最大行索引：{min(analysis_last_row, baseline_last_row)}"
        )
        allure.attach(attach_info, "文件基本信息", allure.attachment_type.TEXT)

    with allure.step("按行号对比字段（平均光强/最大光强/厚度）"):
        differences = compare_by_row(
            analysis_rows,
            analysis_base_indices,
            analysis_thickness_indices,
            analysis_last_row,
            baseline_rows,
            baseline_base_indices,
            baseline_thickness_indices,
            baseline_last_row,
            csv_name,
        )

    with allure.step("校验对比结果，存在差异则用例失败"):
        assert len(differences) == 0, f"CSV存在{len(differences)}处不一致：\n" + "\n".join(differences)
