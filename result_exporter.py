import csv
import os
from typing import List, Dict, Any

class CsvResultExporter:
    """CSV评测结果导出器，Excel打开"""
    def __init__(self, result_list: List[Dict[str, Any]]):
        self.result_list = result_list
        self.export_dir = "./report"
        os.makedirs(self.export_dir, exist_ok=True)

    def export(self, filename: str = "eval_result.csv"):
        """
        导出结果到CSV文件，自动创建report目录
        :param filename: 导出文件名，默认eval_result.csv
        :return: 导出文件的完整路径
        """
        file_path = os.path.join(self.export_dir, filename)
        # CSV表头（和结果字段一一对应）
        headers = [
            "case_id", "case_desc", "execute_timestamp",
            "request_cost_ms", "success_flag", "assert_result",
            "assert_msg", "error_msg"
        ]

        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for res in self.result_list:
                row = {key: res.get(key, "") for key in headers}
                writer.writerow(row)

        print(f"√ CSV报告已导出至：{file_path}")
        return file_path