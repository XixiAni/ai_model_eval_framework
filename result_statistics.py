#批量评测统计
from typing import List, Dict, Any

class ResultStatistics:
    """批量评测结果统计器：纯计算，无副作用"""
    def __init__(self, result_list: List[Dict[str, Any]]):
        self.result_list = result_list
        self.total = len(result_list)
        self.success_count = 0
        self.fail_count = 0
        self.total_cost_ms = 0
        self.avg_cost_ms = 0
        self.max_cost_ms = 0
        self.min_cost_ms = 0

    def calculate(self):
        """执行全量统计"""
        if self.total == 0:
            return self.get_summary()

        cost_list = []
        for res in self.result_list:
            if res.get("success_flag"):
                self.success_count += 1
            else:
                self.fail_count += 1

            cost = res.get("request_cost_ms", 0)
            cost_list.append(cost)
            self.total_cost_ms += cost

        self.max_cost_ms = max(cost_list)
        self.min_cost_ms = min(cost_list)
        self.avg_cost_ms = round(self.total_cost_ms / self.total, 2)

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """获取统计汇总报告"""
        pass_rate = round(self.success_count / self.total * 100, 2) if self.total > 0 else 0.0
        return {
            "总用例数": self.total,
            "成功用例": self.success_count,
            "失败用例": self.fail_count,
            "通过率(%)": pass_rate,
            "总耗时(ms)": self.total_cost_ms,
            "平均耗时(ms)": self.avg_cost_ms,
            "最大耗时(ms)": self.max_cost_ms,
            "最小耗时(ms)": self.min_cost_ms
        }