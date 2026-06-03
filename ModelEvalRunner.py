from typing import List, Dict, Any
import time
# 导入底层请求工具
from api_client_decoupling import AiApiRequest
from assertion_tool import ResponseAssertor
class ModelEvalRunner:
    """
    大模型评测执行器：接收加载好的YAML用例，批量执行API请求、收集结果
    依赖：AiApiRequest（原有底层工具）、YamlCaseLoader（用例加载器）
    """
    def __init__(self, api_client: AiApiRequest):
        # 注入已初始化完成的 AiApiRequest 实例，完全复用原有能力
        self.api_client = api_client
        # 存储所有用例执行结果，后续用于统计、导出CSV
        self.eval_result_list: List[Dict[str, Any]] = []

    def run_single_case(self, case_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行单条YAML用例，返回完整执行结果，自带异常容错"""
        start_time = time.time()
        # 初始化默认结果，异常场景也能正常存入列表
        #兼容 resp 为空、无 code 字段的场景
        single_result = {
            "case_id": case_info.get("case_id", "unknown_id"),
            "case_desc": case_info.get("case_desc", "unknown_desc"),
            "api_path": case_info.get("api_path", ""),
            "request_body": case_info.get("request_body", {}),
            "execute_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "request_cost_ms": 0,
            "api_response": None,
            "success_flag": False,
            "error_msg": "",
            "assert_result": False,
            "assert_msg": "未执行断言"
        }

        try:
            api_path = case_info["api_path"]
            request_body = case_info["request_body"]
            print(f"【评测执行】正在运行用例 {single_result['case_id']}: {single_result['case_desc']}")

            # 调用原有 AiApiRequest 的 send_post 方法，完全复用原有逻辑、日志、异常捕获
            resp = self.api_client.send_post(api_path=api_path, request_data=request_body)
            cost_ms = round((time.time() - start_time) * 1000, 2)

            # 填充正常响应数据
            single_result["request_cost_ms"] = cost_ms
            single_result["api_response"] = resp
            # 兼容 resp 为空、无 code 字段的场景
            if isinstance(resp, dict) and resp.get("code") == 0:
                single_result["success_flag"] = True
            # ============== 新增断言逻辑 ==============
            expect_info = case_info.get("expect", {})
            assertor = ResponseAssertor()
            assert_res, assert_msg = assertor.assert_case(resp, expect_info)
            single_result["assert_result"] = assert_res
            single_result["assert_msg"] = assert_msg
            # ==========================================

        except Exception as e:
            # 捕获全部执行异常，保存错误信息，不会中断批量任务
            single_result["error_msg"] = f"执行异常：{str(e)}"
            print(f"【评测失败】用例 {single_result['case_id']} 运行出错：{str(e)}")

        # 无论成功失败，统一存入结果列表
        self.eval_result_list.append(single_result)
        return single_result

    def run_batch_cases(self, case_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量执行全部YAML用例，返回所有执行结果，单条失败不阻断整体流程"""
        self.eval_result_list.clear()
        print(f"===== 开始批量评测，共加载 {len(case_list)} 条测试用例 =====")
        for case in case_list:
            self.run_single_case(case)
        print(f"===== 批量评测全部完成，总计 {len(self.eval_result_list)} 条执行记录 =====")
        return self.eval_result_list

    def get_all_eval_results(self) -> List[Dict[str, Any]]:
        """对外获取全部执行结果，供给后续统计函数、CSV导出使用"""
        return self.eval_result_list