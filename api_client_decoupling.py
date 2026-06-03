import requests
import json
import warnings
import logging
import time
import os
# 导入 urljoin 解决URL斜杠拼接冲突
from urllib.parse import urljoin
# 导入异常类，统一捕获网络、解析异常
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError

# from dotenv import load_dotenv 移至 main.py ，避免重复加载多次

# 文件顶层全局加载 .env 文件，程序启动一次性执行 存储项目级变量，优先级小于系统变量
# load_dotenv() 括号内可指定文件名'.env.XXX'，移至main.py，避免重复加载多次

# ===================== 新增：日志全局初始化配置（修改日志存储路径） =====================
def init_api_logger():
    # 创建日志对象
    logger = logging.getLogger("AiApiTestLogger")
    logger.setLevel(logging.INFO)
    # 避免重复添加处理器
    if not logger.handlers:
        # 日志格式：时间 | 日志等级 | 信息
        log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        
        # ========== 新增路径逻辑：固定日志到当前项目文件夹 ==========
        # 获取本 api_client_decoupling.py 文件所在的目录（项目根目录）
        current_script_path = os.path.abspath(__file__)
        project_root_dir = os.path.dirname(current_script_path)
        # 拼接日志完整文件路径
        log_full_path = os.path.join(project_root_dir, "api_test.log")
        # =========================================================
        
        # 1. 文件输出，持久化日志（使用固定项目路径）
        file_handler = logging.FileHandler(log_full_path, encoding="utf-8")
        file_handler.setFormatter(log_format)
        # 2. 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

# 全局实例化日志对象
global_logger = init_api_logger()
# =====================================================================

# 消除关闭SSL校验产生的警告
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

class AiApiRequest:
        # 初始化全局配置（AI测开核心配置项）
    def __init__(self, api_key: str = None, base_url: str = "", timeout: int = 30):
        # 绑定全局日志对象(先处理该逻辑防止后面 self.logger.error 无对象)
        self.logger = global_logger
        # 约定系统环境变量名，统一密钥读取入口，修改时仅需改此处
        ENV_API_KEY_NAME = "AI_API_KEY"
        # 优先级：传入参数 > 系统环境变量
        if api_key is not None and api_key.strip() != "":
            self.api_key = api_key.strip()
        else:
            # 读取操作系统环境变量
            env_key = os.getenv(ENV_API_KEY_NAME, "")#格式: os.getenv (环境变量名, 找不到变量时的默认返回值)
            # 为什么返回值设为空>字符串<  为了统一数据类型（始终是字符串），后续用 .strip() 判断空值更方便。
            self.api_key = env_key.strip()
        
        # 密钥非空校验，无可用密钥直接抛出异常
        if not self.api_key:
            err_msg = (f"未获取有效API密钥！请实例化时传入api_key参数/配置系统环境变量 {ENV_API_KEY_NAME}/在项目根目录创建 .env 文件并添加 {ENV_API_KEY_NAME}=你的密钥")
            self.logger.error(err_msg)
            raise ValueError(err_msg)

        # 下方原有全部初始化代码完全保留，无改动
        self.base_url = base_url
        # 全局请求头，默认适配AI接口JSON格式
        self.base_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        # 新增：日志密钥脱敏，防止明文泄露
        # 防止打印请求头导致密钥暴露，例：
        # 错误写法（泄露密钥）
        # self.logger.info(self.base_headers)
        # 正确写法（脱敏，使用预留 masked_auth ）
        # self.logger.info(self.masked_auth)
        self.auth_header = self.base_headers["Authorization"]
        self.masked_auth = self.auth_header[:15] + "***MASKED***" + self.auth_header[-5:]
        # 全局请求超时，支持自定义传入
        self.timeout = timeout
        # 测试环境关闭SSL证书校验
        self.verify = False

        # 创建 Session 会话，复用连接池、自动保存Cookie
        self.session = requests.Session()
        # 给 Session 绑定默认 headers
        self.session.headers.update(self.base_headers)

    # 私有方法：统一解析返回JSON，消除重复代码
    def _parse_response_json(self, resp) -> dict:
        """统一解析接口响应，标准化返回 code/data/msg 三层结构"""
        try:
            result = resp.json()
            return {"code": 0, "data": result, "msg": "请求成功"}
        except json.JSONDecodeError:
            # 接口返回非JSON文本，返回原始内容
            return {
                "code": -2,
                "data": resp.text,
                "msg": "响应内容不是合法JSON格式"
            }

    # 封装通用POST请求（AI大模型接口通常使用POST）
    def send_post(self, api_path: str, request_data: dict):
        """
        发送AI接口POST请求
        :param api_path: 接口路径，若已配置base_url则传路径，否则传完整URL
        :param request_data: 请求体字典，对话、模型参数全部放这里
        :return: 成功返回解析后的JSON字典；失败返回错误信息字典
        """
        # 测试代码 模拟成功响应，跳过真实网络请求,用于框架逻辑调试
        '''return {
            "code": 0,
            "msg": "success",
            "data": {
                "choices": [{"message": {"content": "模拟成功：这是AI的回答"}}]
            }
        }'''
        # 修复：使用 urljoin 替代字符串相加，自动处理首尾斜杠冲突
        full_url = urljoin(self.base_url, api_path)
        # ===================== 新增：请求计时 + 日志打印 =====================
        start_time = time.time()
        # ===================== 新增：自动重试配置（网络抖动保护） =====================
        max_retry = 1       # 最多重试1次
        retry_count = 0     # 当前重试次数
        retry_interval = 1  # 重试间隔1秒

        self.logger.info(f"【POST请求发起】接口地址：{full_url}，请求入参：{request_data}")

        # ===================== 重试循环 =====================
        # 思路:仅捕获【超时/网络错误】进行重试，其他异常直接返回
        while retry_count <= max_retry:
            try:
                # 使用 session 发起请求，全局配置自动生效
                resp = self.session.post(
                    url=full_url,
                    json=request_data,
                    timeout=self.timeout,
                    verify=self.verify
                )
                # 自动校验200~299状态码，非成功码直接抛出异常
                resp.raise_for_status()
                parse_result = self._parse_response_json(resp)
                cost = round((time.time() - start_time) * 1000, 2)
                self.logger.info(f"【POST请求完成】耗时{cost}ms，返回状态码：{resp.status_code}，统一返回码：{parse_result['code']}")
                return parse_result

            # 只捕获【超时/网络错误】进行重试，其他异常直接返回
            except (Timeout, ConnectionError) as e:
                retry_count += 1
                # 重试次数用完，不再试，跳出循环走最终异常逻辑
                if retry_count > max_retry:
                    break
                # 重试前等待，打印警告日志
                self.logger.warning(f"网络波动，{retry_interval}秒后重试第 {retry_count} 次...")
                time.sleep(retry_interval)

        # ===================== 最终异常处理（重试失败后统一返回） =====================
        cost = round((time.time() - start_time) * 1000, 2)
        try:
            # 重试后依然失败，强制触发最终异常返回
            resp.raise_for_status()
        except Timeout:
            err_msg = f"请求超时，超时限制{self.timeout}秒"
            self.logger.error(f"【POST请求失败】接口：{full_url}，耗时{cost}ms，错误原因：{err_msg}")
            return {"code": -1, "data": None, "msg": err_msg}
        except ConnectionError:
            err_msg = "网络连接失败，无法访问接口地址"
            self.logger.error(f"【POST请求失败】接口：{full_url}，耗时{cost}ms，错误原因：{err_msg}")
            return {"code": -1, "data": None, "msg": err_msg}
        except HTTPError as e:
            err_msg = f"接口返回错误状态码：{str(e)}"
            self.logger.error(f"【POST请求失败】接口：{full_url}，耗时{cost}ms，错误原因：{err_msg}，原始响应：{resp.text}")
            return {"code": -1, "data": resp.text, "msg": err_msg}
        except RequestException as e:
            err_msg = f"未知网络异常：{str(e)}"
            self.logger.error(f"【POST请求失败】接口：{full_url}，耗时{cost}ms，错误原因：{err_msg}")
            return {"code": -1, "data": None, "msg": err_msg}
    
    # 拓展：封装GET请求，用于查询类辅助接口
    def send_get(self, api_path: str, params: dict = None):
        """
        发送GET请求，用于查询类辅助接口
        :param api_path: 接口路径/完整URL
        :param params: URL查询参数字典
        :return: 标准化响应字典
        """
        # 修复：使用 urljoin 替代字符串相加
        full_url = urljoin(self.base_url, api_path)
        # ===================== 新增：请求计时 + 日志打印 =====================
        start_time = time.time()
        self.logger.info(f"【GET请求发起】接口地址：{full_url}，查询参数：{params}")
        try:
            resp = self.session.get(
                url=full_url,
                params=params,
                timeout=self.timeout,
                verify=self.verify
            )
            resp.raise_for_status()
            parse_result = self._parse_response_json(resp)
            cost = round((time.time() - start_time) * 1000, 2)
            self.logger.info(f"【GET请求完成】耗时{cost}ms，返回状态码：{resp.status_code}，统一返回码：{parse_result['code']}")
            return parse_result
        except RequestException as e:
            cost = round((time.time() - start_time) * 1000, 2)
            err_msg = f"请求异常：{str(e)}"
            self.logger.error(f"【GET请求失败】接口：{full_url}，耗时{cost}ms，错误原因：{err_msg}")
            return {"code": -1, "data": None, "msg": err_msg}


# code=0 / -1 / -2 编码定义
# 不属于行业强制标准，面向AI自动化测试场景自定义分层状态码： 
# code = 0 ：全流程正常（网络连通、HTTP状态码合法、返回内容为标准JSON），测试用例断言  res["code"] == 0  判定接口调用成功；
# code = -1 ：网络/HTTP链路故障（超时、连接失败、4xx/5xx错误码、其他网络异常），HTTP请求根本没有拿到合法2xx响应；
# code = -2 ：HTTP通信成功（拿到2xx状态码），但返回内容无法解析为JSON，属于业务数据格式异常。
# 返回字典中  data  字段作用
# 用于存放原始有效数据，方便测试脚本打印日志、排查缺陷：
# code=0 ：data = 接口返回的完整JSON字典，直接提取模型回答、token消耗等业务字段；
# code=-2 ：data = resp.text 原始响应文本，用于查看接口返回的非JSON报错文本；
# code=-1 ：data = None，链路层面完全没拿到响应内容，无原始数据可存储。

# yaml功能块
import yaml
from typing import List, Dict, Any

class YamlCaseLoader:
    """
    YAML测试用例加载器：独立模块，仅负责读取、解析yaml评测用例文件
    完全解耦，不依赖AiApiRequest底层请求工具
    """
    def __init__(self, yaml_file_path: str):
        self.yaml_file_path = yaml_file_path
        self.logger = logging.getLogger("AiApiTestLogger")
        self.REQUIRED_FIELDS = ["case_id", "case_desc", "api_path", "request_body"]
    def load_all_cases(self) -> List[Dict[str, Any]]:
        """读取yaml文件，返回标准化用例列表"""
        try:
            self.logger.info(f"开始读取YAML用例文件: {self.yaml_file_path}")
            with open(self.yaml_file_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
            # 取出根节点 case_list 下的所有用例
            case_list = yaml_data.get("case_list", [])
            valid_cases = []
            for case in case_list:
                missing = [f for f in self.REQUIRED_FIELDS if f not in case]
                if missing:
                    self.logger.warning(f"单条用例缺失必填字段 {missing}，跳过该用例")
                    continue
                valid_cases.append(case)
            self.logger.info(f"文件原始用例数:{len(case_list)}, 合法可用用例数:{len(valid_cases)}")
            # 返回替换为合法用例列表
            return valid_cases
        except FileNotFoundError:
            self.logger.error(f"用例文件不存在：{self.yaml_file_path}")
            raise FileNotFoundError(f"用例文件不存在：{self.yaml_file_path}")
        except yaml.YAMLError as e:
            self.logger.error(f"YAML文件格式错误：{str(e)}")
            raise ValueError(f"YAML文件格式错误：{str(e)}")