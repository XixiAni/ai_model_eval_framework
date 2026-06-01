#自动将所有用例结果导出为CSV，使用Excel打开后可直接查看、筛选、统计，极大提升评测结果的可用性和分析效率
import csv
import os
from typing import List, Dict, Any

class CsvResultExporter:
    """CSV评测结果导出器"""
    def __init__(self, result_list: List[Dict[str, Any]]):
        self.result_list = result_list
        self.export_dir = "./report"
        os.makedirs(self.export_dir, exist_ok=True)

    def export(self, filename: str = "eval_result.csv"):
        """导出到 report/eval_result.csv"""
        file_path = os.path.join(self.export_dir, filename)
        # CSV表头（和结果字段一一对应）
        headers = [
            "case_id", "case_desc", "execute_timestamp",
            "request_cost_ms", "success_flag", "assert_result"
            "assert_msg","error_msg"
        ]

        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for res in self.result_list:
                row = {key: res.get(key, "") for key in headers}
                writer.writerow(row)

        print(f"√ CSV报告已导出至：{file_path}")
        return file_path