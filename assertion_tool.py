#读取 YAML 里的  expect  字段，自动做响应校验，实现：
 
#- code 断言（必须=0）

#- 包含关键词（content 包含某段话）

#- 字段存在性校验
from typing import Dict, Any

class ResponseAssertor:
    """通用响应断言工具：读取YAML expect字段自动校验"""
    def __init__(self):
        self.assert_result = True
        self.assert_msg = "断言通过"

    def assert_case(self, response: Dict[str, Any], expect: Dict[str, Any]) -> tuple[bool, str]:
        """
        执行单条用例断言
        :param response: api_response 原始响应
        :param expect: YAML中的expect配置
        :return: (断言是否通过, 断言信息)
        """
        self.assert_result = True
        self.assert_msg = []

        # 1. 断言code必须为0
        exp_code = expect.get("code", 0)
        if response.get("code") != exp_code:
            self.assert_result = False
            self.assert_msg.append(f"code断言失败：期望={exp_code}, 实际={response.get('code')}")

        # 2. 断言返回内容包含关键词
        exp_contains = expect.get("contains", [])
        if exp_contains and isinstance(exp_contains, list):
            try:
                content = response["data"]["choices"][0]["message"]["content"]
                for keyword in exp_contains:
                    if keyword not in content:
                        self.assert_result = False
                        self.assert_msg.append(f"关键词缺失：{keyword}")
            except Exception as e:
                self.assert_result = False
                self.assert_msg.append(f"提取响应内容失败：{str(e)}")

        # 3. 组装最终消息
        final_msg = " | ".join(self.assert_msg) if self.assert_msg else "断言通过"
        return self.assert_result, final_msg