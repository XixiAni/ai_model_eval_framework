# AI大模型接口自动化评测框架（YAML数据驱动版）
> 最后更新时间：2026年6月 | 版本：v1.1
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

基于 Python + Requests 开发的企业级AI大模型接口自动化测试框架，采用分层解耦+数据驱动设计，实现用例与代码完全分离，支持批量自动执行、智能断言、多维统计与CSV报告导出，适用于大模型API自动化评测、回归测试、性能监控场景。
 

## 1 🚀 快速上手
 
1. 安装依赖

请确保本地已安装Python 3.8+环境
```bash
pip install requests python-dotenv pyyaml
```

2. 配置密钥
 
项目根目录创建  .env  文件（复制 .env.example 模板修改即可）：
 
```ini
AI_API_KEY=sk-DeepSeek密钥
```
 
3. 运行项目
 
```bash
python main.py
```
 
4. 查看结果
 
- 控制台输出：实时执行日志 + 通过率/耗时统计报告
- CSV报告： ./report/eval_result.csv （Excel打开）
- 全链路日志： ./api_test.log 
 
 
## 2 ✨ 核心功能亮点
 
1. YAML数据驱动：用例与代码完全分离，非技术人员也能编写维护测试用例
2. 统一请求封装：标准化 code/data/msg 三层返回结构，统一处理鉴权、日志、异常、超时
3. 高容错批量执行：单条用例失败不中断整批任务，支持网络异常自动重试
4. 通用断言工具：支持响应码校验、返回内容关键词校验，自动生成断言结果
5. 多维统计与报告：自动计算通过率、平均耗时、最大/最小耗时，导出Excel兼容的CSV报告
6. 企业级安全规范：密钥通过环境变量读取，无硬编码；预留日志密钥脱敏机制
 
 
## 3 📁 项目目录结构
 
```plaintext 
├── main.py                  # 项目唯一入口，负责环境初始化与模块调度
├── api_client_decoupling.py # 底层核心：接口请求工具 + YAML用例加载器
├── ModelEvalRunner.py       # 业务核心：批量评测执行器
├── assertion_tool.py        # 工具层：通用响应断言工具
├── result_statistics.py     # 工具层：批量评测统计工具
├── result_exporter.py       # 工具层：CSV报告导出工具
├── chat_cases_new.yaml      # 数据层：YAML测试用例集
├── .env                     # 配置文件：API密钥（禁止提交仓库）
├── .env.example             # 密钥配置模板（可提交仓库）
└── .gitignore
```


## 4 📚 代码架构与实现思路
 
### 4.1 分层架构
 
```plaintext
入口层(main.py) → 核心执行层(api_client_decoupling.py + ModelEvalRunner.py) → 工具层(断言/统计/导出)
```
 
### 4.2 五大设计原则
 
- 依赖注入：ModelEvalRunner 不直接实例化 AiApiRequest ，而是接收外部传入的实例，实现解耦
- 数据驱动：所有测试用例写在YAML文件，与代码完全分离
- 统一返回格式：所有接口请求统一返回 code/data/msg 三层结构
- 高容错：单条用例执行异常不中断整批任务
- 无侵入扩展：统计、导出、断言模块完全独立，仅接收执行结果作为输入
 

## 5 ⚙️ 各模块详细说明

### 5.1 入口层：main.py
 
文件职责：程序启动入口，负责环境初始化、模块调度、结果输出
核心执行顺序：
 
1. 环境变量加载
- 通过 os.path.abspath(__file__) 获取自身绝对路径，定位项目根目录
- 调用 dotenv.load_dotenv() 加载同级目录下的 .env 文件
- 优先级：系统环境变量 > .env 文件变量
2. 单接口调试（可选）
- 实例化 AiApiRequest （自动读取 AI_API_KEY 环境变量）
- 构造请求参数字典 chat_params 
- 调用 api_client.send_post() 发起请求
- 根据返回 code 字段判断请求结果，打印并记录日志
3. YAML用例加载
- 拼接YAML用例文件绝对路径 yaml_path 
- 实例化 YamlCaseLoader ，传入文件路径
- 调用 case_loader.load_all_cases()  读取并校验用例
- 异常处理：文件不存在、YAML格式错误、无可用用例时直接退出
4. 批量评测执行
- 实例化 ModelEvalRunner ，注入已初始化的 AiApiRequest 实例
- 调用 eval_runner.run_batch_cases(case_list)  批量执行所有用例
- 接收返回值 result_list （所有用例执行结果的字典列表）
5. 结果处理与输出
- 基础统计：手动计算总用例数、成功数、失败数、通过率
- 高级统计：实例化 ResultStatistics(result_list) ，调用 calculate() 生成详细统计报告
- CSV导出：实例化 CsvResultExporter(result_list) ，调用 export() 生成报告文件
 
### 5.2 底层核心：api_client_decoupling.py
 
文件职责：封装AI接口请求、日志管理、YAML用例加载
包含两个独立类： AiApiRequest + YamlCaseLoader 
 
#### 5.2.1 AiApiRequest（接口请求工具类）
 
核心功能：统一处理HTTP请求、日志、异常、响应解析
 
1. 全局日志初始化
- 顶层函数 init_api_logger() 创建全局单例日志对象 global_logger 
- 支持控制台+文件双输出，日志文件固定在项目根目录 api_test.log 
- 防重复处理器逻辑，避免多次实例化导致日志重复打印
2. init 初始化方法
- 密钥读取优先级：实例化传入的 api_key > 系统环境变量 AI_API_KEY 
- 无有效密钥时抛出 ValueError 并记录ERROR日志
- 初始化全局请求头 base_headers ，自动添加Bearer鉴权
- 密钥脱敏：生成 masked_auth 变量（前15位+MASKED+后5位），仅用于日志打印
- 初始化 requests.Session ，绑定全局请求头、超时、SSL配置
3. _parse_response_json（私有方法）
- 统一解析接口响应，标准化返回格式
- 成功解析JSON：返回  {"code":0, "data":json_dict, "msg":"请求成功"} 
- 解析失败：返回  {"code":-2, "data":resp.text, "msg":"响应内容不是合法JSON格式"} 
4. send_post（核心请求方法）
- 入参： api_path （接口路径/完整URL）、 request_data （请求体字典）
- 使用 urljoin 拼接 base_url 和 api_path ，自动处理斜杠冲突
- 自动重试逻辑：
- 配置 max_retry=1 、 retry_interval=1 
- 仅捕获 Timeout 和 ConnectionError 进行重试
- 重试失败后跳出循环，进入统一异常处理
- 调用 resp.raise_for_status()  自动校验2xx状态码
- 计算请求耗时（毫秒），记录INFO日志
- 异常分层处理：超时/连接错误/HTTP错误/未知异常，统一返回  code=-1 
5. send_get（辅助请求方法）
- 逻辑与 send_post 一致，支持URL查询参数
- 无自动重试逻辑
 
#### 5.2.2 YamlCaseLoader（用例加载器）
 
核心功能：读取YAML文件、校验用例合法性、过滤非法用例
 
1. init 初始化
- 接收YAML文件路径 yaml_file_path 
- 定义必填字段常量 REQUIRED_FIELDS = ["case_id", "case_desc", "api_path", "request_body"] 
2. load_all_cases（核心方法）
- 读取YAML文件，解析为Python字典
- 提取根节点 case_list 下的所有用例
- 逐条校验必填字段，缺失字段的用例跳过并记录WARNING日志
- 返回合法用例列表 valid_cases 
- 异常处理：文件不存在抛出 FileNotFoundError ，格式错误抛出 ValueError 
 
### 5.3 执行引擎：ModelEvalRunner.py

文件职责：循环执行YAML用例、收集执行结果、调用断言工具
核心设计：完全依赖注入，不直接依赖任何底层实现
 
1. init 初始化
- 接收外部传入的 AiApiRequest 实例 api_client 
- 初始化结果列表 self.eval_result_list ，存储所有用例执行结果
2. run_single_case（单条用例执行）
- 入参：单条用例字典 case_info 
- 初始化默认结果字典 single_result ，包含所有必填字段
- 调用 self.api_client.send_post() 发起请求，传入 api_path 和 request_body 
- 填充请求耗时、响应数据、成功标记（ resp.get("code") == 0 ）
- 断言逻辑：
- 提取用例中的 expect 字段
- 实例化 ResponseAssertor 
- 调用 assertor.assert_case(resp, expect_info) 执行断言
- 将断言结果 assert_result 和 assert_msg 存入 single_result 
- 捕获所有执行异常，记录错误信息，不中断流程
- 将结果添加到 self.eval_result_list 并返回
3. run_batch_cases（批量执行）
- 入参：合法用例列表 case_list 
- 清空历史结果列表
- 循环调用 run_single_case() 执行每条用例
- 返回完整结果列表 self.eval_result_list 
4. get_all_eval_results
- 对外暴露结果列表，供统计、导出模块使用
 
### 5.4 工具1：断言模块 assertion_tool.py
 
文件职责：读取YAML中的expect字段，自动校验响应结果
核心方法： assert_case(response, expect) 
 
- 入参： response （ AiApiRequest 返回的标准化响应）、 expect （YAML中的断言配置）
- 支持两种断言类型：
1. code断言：默认期望 code=0 ，可通过 expect["code"] 自定义
2. 关键词包含断言：校验响应内容包含 expect["contains"] 列表中的所有关键词
- 异常处理：提取响应内容失败时标记断言失败
- 返回值：元组  (assert_result: bool, assert_msg: str) 
 
### 5.5 工具2：统计模块 result_statistics.py
 
文件职责：基于执行结果计算多维统计指标
核心方法： calculate() 
 
- 遍历 result_list ，统计成功数、失败数、总耗时
- 计算平均耗时、最大耗时、最小耗时、通过率
- 返回结构化统计字典，包含8项核心指标
 
### 5.6 工具3：导出模块 result_exporter.py
 
文件职责：将执行结果导出为CSV文件
核心方法： export(filename) 
 
- 自动创建  ./report  目录
- 导出字段： case_id 、 case_desc 、 execute_timestamp 、 request_cost_ms 、 success_flag 、 assert_result 、 assert_msg 、 error_msg 
- 使用  utf-8-sig  编码，Excel直接打开无乱码
- 返回导出文件的完整路径
 
### 5.7 用例层：chat_cases_new.yaml
 
文件格式规范：
 
- 根节点必须为  case_list 
- 每条用例必须包含 case_id 、 case_desc 、 api_path 、 request_body 四个必填字段
-  request_body 完全兼容DeepSeek官方API格式
-  expect 字段为可选，用于断言配置

示例：
```yaml
case_list:
  - case_id: AI_TEST_001
    case_desc: 大模型问答测试
    api_path: /v1/chat/completions
    request_body:
      model: deepseek-v4-flash
      messages: [{role:user, content:"测试内容"}]
    expect:
      code: 0
      contains: ["测试"]
```

## 6 🧾 全链路执行流程（数据流向）
 
```plaintext
1. main.py 加载.env → 初始化 AiApiRequest
2. main.py → YamlCaseLoader.load_all_cases() → 合法用例列表 case_list
3. main.py → ModelEvalRunner(api_client) → 注入依赖
4. ModelEvalRunner.run_batch_cases(case_list)
   → 循环调用 run_single_case(case)
      → AiApiRequest.send_post() → 标准化响应 resp
      → ResponseAssertor.assert_case(resp, expect) → 断言结果
      → 生成 single_result → 加入 eval_result_list
5. ModelEvalRunner 返回 result_list 给 main.py
6. main.py → ResultStatistics(result_list).calculate() → 统计报告
7. main.py → CsvResultExporter(result_list).export() → CSV报告
8. main.py 控制台输出所有结果
```
 
 
## 7 📌 核心数据结构说明
 
### 7.1 接口统一返回格式
 
```python
{
    "code": int,       # 0=成功, -1=网络错误, -2=JSON解析错误
    "data": Any,       # 成功=响应JSON, 失败=原始文本/None
    "msg": str         # 结果描述
}
```
 
### 7.2 单条用例执行结果格式
 
```python
{
    "case_id": str,
    "case_desc": str,
    "api_path": str,
    "request_body": dict,
    "execute_timestamp": str,
    "request_cost_ms": float,
    "api_response": dict,  # 接口统一返回格式
    "success_flag": bool,
    "error_msg": str,
    "assert_result": bool,
    "assert_msg": str
}
```
 

## 8 💡 关键设计思路说明
 
1. 依赖注入： ModelEvalRunner 不直接创建 AiApiRequest 实例，方便后续替换不同的请求实现或进行单元测试
2. 统一返回格式：所有接口请求返回相同结构，上层代码无需处理不同的响应格式，断言逻辑更简单
3. 异常隔离：单条用例的异常被限制在 run_single_case 内部，不会影响其他用例执行
4. 纯工具类设计：断言、统计、导出模块均为无状态类，仅接收输入并返回结果，无副作用，易于测试和复用
5. 安全设计：密钥不硬编码，通过环境变量读取；预留密钥脱敏机制，防止日志泄露
 
 
## 9 📖 详细文档
完整的功能说明、配置参数、代码逻辑详解请查看：[详细使用手册](docs/DETAILED_USAGE.md)


## 10 📝 许可证 & 📧 联系方式
MIT License
邮箱：3549637968@qq.com，如有问题或建议，欢迎提交Issue或PR