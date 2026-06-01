import os
# 新增：加载本地.env文件密钥配置
from dotenv import load_dotenv
# 1. 获取main.py完整绝对路径
current_script_abs_path = os.path.abspath(__file__)
# 2. 提取main.py所在的项目文件夹路径
current_dir = os.path.dirname(current_script_abs_path)
# 3. 拼接出和main.py同级的.env文件完整路径
env_path = os.path.join(current_dir, ".env")
# 4. 强制指定路径加载.env文件，不再依赖终端目录
load_dotenv(dotenv_path=env_path)

from api_client_decoupling import AiApiRequest,YamlCaseLoader
from ModelEvalRunner import ModelEvalRunner
from result_statistics import ResultStatistics
from result_exporter import CsvResultExporter
# ---------------- 框架调用示例（两种模式：手动传密钥 / 环境变量自动读取） ----------------
if __name__ == "__main__":
    # ========== 模式1：原有方式，手动传入密钥（本地临时调试用） ==========
    # model_api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # api_client = AiApiRequest(api_key=model_api_key, base_url="https://api.deepseek.com")

    # ========== 模式2：新增安全方式，自动读取系统环境变量/.env文件的 AI_API_KEY ==========
    # Windows临时设置环境变量命令（cmd）：set AI_API_KEY=sk-xxxxxxxxxxxx
    # Windows PowerShell临时设置：$env:AI_API_KEY="sk-xxxxxxxxxxxx"
    api_client = AiApiRequest(base_url="https://api.deepseek.com")

    # ---------------- 接口地址两种传入方式说明 ----------------
    # 方式一：初始化时传入base_url，send_post仅填写接口短路径（推荐，统一管理域名）
    chat_path = "/v1/chat/completions"
    # 方式二：初始化不填base_url，send_post传入完整接口地址
    # chat_path = "https://api.deepseek.com/v1/chat/completions"

    # 2. 构造AI对话请求参数
    chat_params = {
        "model": "deepseek-v4-flash",
        "messages": [
            {"role": "user", "content": "简单介绍AI测试开发"}
        ],
        "temperature": 0.7
    }
    # 3. 发起请求，接收统一格式返回结果
    res = api_client.send_post(api_path=chat_path, request_data=chat_params)
    # 4. 自动化测试判断逻辑：根据返回code校验请求是否成功
    if res["code"] == 0:
        print("接口调用成功，模型返回内容：")
        print(res["data"]["choices"][0]["message"]["content"])
        api_client.logger.info("【测试用例执行成功】")
    else:
        print(f"接口调用失败，错误信息：{res['msg']}")
        print(f"原始响应数据：{res['data']}")
        api_client.logger.error(f"【测试用例执行失败】错误消息：{res['msg']}，原始数据：{res['data']}")
    print("\n" + "="*60)
    # ====================== 项目一核心：YAML数据驱动批量评测（追加部分） ======================
    # 1. 加载YAML测试用例文件
    yaml_path = os.path.join(current_dir, "chat_cases_new.yaml")
    case_loader = YamlCaseLoader(yaml_file_path=yaml_path)
    try:
        # 读取并校验所有用例
        case_list = case_loader.load_all_cases()
    except Exception as e:
        print(f"YAML用例加载失败：{e}")
        exit(1)
    if not case_list:
        print("无可用测试用例")
        exit(0)
    # 2. 初始化批量评测执行器
    eval_runner = ModelEvalRunner(api_client=api_client)
    # 3. 批量执行所有YAML用例
    result_list = eval_runner.run_batch_cases(case_list=case_list)
    # 4. 批量结果汇总（项目亮点）
    total = len(result_list)
    success = sum(1 for item in result_list if item["success_flag"])
    fail = total - success
    print("\n" + "="*60)
    print("【批量评测汇总结果】")
    print(f"总用例数：{total}")
    print(f"成功用例：{success}")
    print(f"失败用例：{fail}")
    print(f"通过率：{success/total*100:.2f}%" if total > 0 else "通过率：0%")
    print("="*60)
    # ====================== 新增功能集成：统计 + 导出 + 断言 ======================
    # 1. 批量统计
    stats = ResultStatistics(result_list)
    summary = stats.calculate()
    print("\n 批量评测统计报告：")
    for k, v in summary.items():
        print(f"{k}: {v}")

    # 2. 导出CSV
    exporter = CsvResultExporter(result_list)
    exporter.export()
