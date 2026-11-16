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
ANALYSIS_NAME = "EpdAnalysis_5.0.0(测试DA3.3V1接口)"


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
    """读取CSV，返回行数据、基础字段索引、厚度字段索引、编码、各字段最后有效行字典"""
    for encoding in ["utf-8-sig", "gbk", "gb2312"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                rows = [row for row in reader]

            if not rows:
                return rows, {}, {}, encoding, {}

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

            # 每个字段独立计算最后有效行（互不影响）
            field_last_rows = {}

            for field, col_idx in base_indices.items():
                last_row_idx = 0
                for row_idx in range(1, len(rows)):
                    row = rows[row_idx]
                    if col_idx < len(row) and row[col_idx].strip():
                        last_row_idx = row_idx
                field_last_rows[field] = last_row_idx
                logger.debug(
                    f"{file_path} 中 {field} 的最后有效行索引：{last_row_idx}"
                )

            for thick_field, thick_idx in thickness_indices.items():
                last_thick_row_idx = 0
                for row_idx in range(1, len(rows)):
                    row = rows[row_idx]
                    if thick_idx < len(row) and row[thick_idx].strip():
                        last_thick_row_idx = row_idx
                field_last_rows[thick_field] = last_thick_row_idx
                logger.debug(
                    f"{file_path} 中 {thick_field} 的最后有效行索引：{last_thick_row_idx}"
                )

            return rows, base_indices, thickness_indices, encoding, field_last_rows

        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法读取文件 {file_path}，编码不支持")


def compare_by_row(
    analysis_rows,
    analysis_base_indices,
    analysis_thickness_indices,
    analysis_field_last_rows,
    baseline_rows,
    baseline_base_indices,
    baseline_thickness_indices,
    baseline_field_last_rows,
    csv_name,
):
    """按行号对比目标字段列。光强0容忍，厚度允许≤0.00010001误差。
    每个字段独立按自己的有效行范围对比，避免某个字段截断其他字段。"""
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

    # 收集所有需要对比的字段（基础字段 + 共同厚度字段）
    all_fields = {}
    for field in BASE_TARGET_FIELDS:
        if field in analysis_base_indices and field in baseline_base_indices:
            all_fields[field] = (
                analysis_base_indices[field],
                baseline_base_indices[field],
            )
    for field in common_thickness_fields:
        all_fields[field] = (
            analysis_thickness_indices[field],
            baseline_thickness_indices[field],
        )

    if not all_fields:
        msg = "无共同字段可对比（基础字段和厚度字段均无交集）"
        differences.append(msg)
        logger.error(f"{csv_name}：{msg}")
        return differences

    # 逐字段独立对比：每个字段按自己的有效行范围比较
    for field, (analysis_col_idx, baseline_col_idx) in all_fields.items():
        analysis_last = analysis_field_last_rows.get(field, 0)
        baseline_last = baseline_field_last_rows.get(field, 0)
        field_max_row = min(analysis_last, baseline_last)

        if field_max_row < 1:
            msg = (
                f"字段 '{field}' 无有效数据行可对比"
                f"（分析文件最后有效行={analysis_last}，基准文件={baseline_last}）"
            )
            differences.append(msg)
            logger.warning(f"{csv_name}：{msg}")
            continue

        is_thickness = field in common_thickness_fields

        for row_idx in range(1, field_max_row + 1):
            row_num = row_idx + 1

            analysis_row = analysis_rows[row_idx] if row_idx < len(analysis_rows) else []
            baseline_row = baseline_rows[row_idx] if row_idx < len(baseline_rows) else []

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
                if is_thickness:
                    error = abs(analysis_float - baseline_float)
                    is_same = error <= THICKNESS_ERROR_THRESHOLD
                else:
                    is_same = analysis_float == baseline_float
            except (ValueError, TypeError):
                is_same = analysis_val == baseline_val

            if not is_same:
                if is_thickness and error is not None:
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（误差{error:.8f} > {THICKNESS_ERROR_THRESHOLD}）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )
                elif is_thickness:
                    msg = (
                        f"行号 {row_num}，字段 '{field}' 不一致（非数值/空值）：\n"
                        f"  {ANALYSIS_NAME}：'{analysis_val}'\n"
                        f"  {BASELINE_NAME}：'{baseline_val}'"
                    )
                else:
                    try:
                        float(analysis_val)
                        float(baseline_val)
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

    with allure.step("读取CSV完整行数据及字段信息"):
        (
            analysis_rows,
            analysis_base_indices,
            analysis_thickness_indices,
            analysis_encoding,
            analysis_field_last_rows,
        ) = read_csv_by_rows(analysis_file)

        (
            baseline_rows,
            baseline_base_indices,
            baseline_thickness_indices,
            baseline_encoding,
            baseline_field_last_rows,
        ) = read_csv_by_rows(baseline_file)

        analysis_thickness_fields = list(analysis_thickness_indices.keys())
        baseline_thickness_fields = list(baseline_thickness_indices.keys())
        common_thickness_fields = list(
            set(analysis_thickness_fields) & set(baseline_thickness_fields)
        )

        # 每个字段的对比截止行（取两文件该字段最后有效行的min）
        field_compare_rows = {}
        for field in list(BASE_TARGET_FIELDS) + common_thickness_fields:
            a_last = analysis_field_last_rows.get(field, 0)
            b_last = baseline_field_last_rows.get(field, 0)
            field_compare_rows[field] = min(a_last, b_last)

        attach_info = (
            f"=== {ANALYSIS_NAME} ===\n"
            f"编码：{analysis_encoding}\n"
            f"基础字段：{list(analysis_base_indices.keys())}\n"
            f"厚度字段：{analysis_thickness_fields}\n"
            f"各字段最后有效行：{analysis_field_last_rows}\n\n"
            f"=== {BASELINE_NAME} ===\n"
            f"编码：{baseline_encoding}\n"
            f"基础字段：{list(baseline_base_indices.keys())}\n"
            f"厚度字段：{baseline_thickness_fields}\n"
            f"各字段最后有效行：{baseline_field_last_rows}\n\n"
            f"=== 对比规则 ===\n"
            f"共同厚度字段：{common_thickness_fields}\n"
            f"厚度误差阈值：≤{THICKNESS_ERROR_THRESHOLD}\n"
            f"各字段对比截止行：{field_compare_rows}"
        )
        allure.attach(attach_info, "文件基本信息", allure.attachment_type.TEXT)

    with allure.step("按行号对比字段（平均光强/最大光强/厚度）"):
        differences = compare_by_row(
            analysis_rows,
            analysis_base_indices,
            analysis_thickness_indices,
            analysis_field_last_rows,
            baseline_rows,
            baseline_base_indices,
            baseline_thickness_indices,
            baseline_field_last_rows,
            csv_name,
        )

    with allure.step("校验对比结果，存在差异则用例失败"):
        assert len(differences) == 0, f"CSV存在{len(differences)}处不一致：\n" + "\n".join(differences)