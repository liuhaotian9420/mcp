# 📝 MCP-CLI 最佳实践指南

本指南涵盖了使用 MCP-CLI 开发高质量服务的最佳实践，帮助您构建可维护、可扩展、高性能的 MCP 服务。

## 📋 目录

- [代码组织与结构](#代码组织与结构)
- [函数设计原则](#函数设计原则)
- [类型注解与文档](#类型注解与文档)
- [错误处理策略](#错误处理策略)
- [性能优化技巧](#性能优化技巧)
- [安全性考虑](#安全性考虑)
- [测试策略](#测试策略)
- [部署与运维](#部署与运维)
- [常见陷阱与避免方法](#常见陷阱与避免方法)

## 代码组织与结构

### 🏗️ 推荐的项目结构

#### 小型项目（< 10个工具）
```
my_mcp_service/
├── tools.py              # 所有工具函数
├── requirements.txt       # 依赖管理
├── .env                  # 环境变量
├── README.md             # 项目说明
└── tests/
    ├── test_tools.py     # 测试文件
    └── __init__.py
```

#### 中型项目（10-30个工具）
```
my_mcp_service/
├── tools/
│   ├── __init__.py
│   ├── math_utils.py     # 数学工具
│   ├── text_utils.py     # 文本处理
│   ├── data_utils.py     # 数据处理
│   └── web_utils.py      # 网络工具
├── common/
│   ├── __init__.py
│   ├── validators.py     # 输入验证
│   ├── exceptions.py     # 自定义异常
│   └── helpers.py        # 辅助函数
├── config/
│   ├── __init__.py
│   ├── settings.py       # 配置管理
│   └── constants.py      # 常量定义
├── tests/
│   ├── test_math_utils.py
│   ├── test_text_utils.py
│   └── test_data_utils.py
├── requirements.txt
├── .env.example
└── README.md
```

#### 大型项目（> 30个工具）
```
enterprise_mcp_service/
├── services/
│   ├── math/
│   │   ├── __init__.py
│   │   ├── basic.py      # 基础数学运算
│   │   ├── advanced.py   # 高级数学函数
│   │   └── statistics.py # 统计分析
│   ├── text/
│   │   ├── __init__.py
│   │   ├── processing.py # 文本处理
│   │   ├── analysis.py   # 文本分析
│   │   └── nlp.py        # 自然语言处理
│   ├── data/
│   │   ├── __init__.py
│   │   ├── csv_utils.py  # CSV处理
│   │   ├── json_utils.py # JSON处理
│   │   └── db_utils.py   # 数据库操作
│   └── external/
│       ├── __init__.py
│       ├── api_client.py # API客户端
│       └── webhooks.py   # Webhook处理
├── core/
│   ├── __init__.py
│   ├── base.py           # 基础类
│   ├── validators.py     # 输入验证
│   ├── exceptions.py     # 异常定义
│   └── middleware.py     # 中间件
├── config/
│   ├── __init__.py
│   ├── settings.py       # 设置管理
│   ├── logging.py        # 日志配置
│   └── security.py       # 安全配置
├── tests/
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── e2e/            # 端到端测试
├── docs/
│   ├── api.md          # API文档
│   └── deployment.md   # 部署文档
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── start.sh        # 启动脚本
│   └── deploy.sh       # 部署脚本
├── requirements/
│   ├── base.txt        # 基础依赖
│   ├── dev.txt         # 开发依赖
│   └── prod.txt        # 生产依赖
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

### 🎯 命名规范

#### 文件命名
```python
# ✅ 好的命名
math_utils.py      # 清晰表达功能
text_processing.py # 描述性命名
data_analysis.py   # 一目了然

# ❌ 避免的命名
utils.py          # 过于泛化
helpers.py        # 含义模糊
tools.py          # 不够具体（除非是小项目）
```

#### 函数命名
```python
# ✅ 好的命名
def calculate_compound_interest(principal: float, rate: float, time: float) -> float:
    """计算复利"""
    pass

def extract_email_addresses(text: str) -> List[str]:
    """从文本中提取邮箱地址"""
    pass

def convert_csv_to_json(csv_file_path: str) -> dict:
    """将CSV文件转换为JSON格式"""
    pass

# ❌ 避免的命名
def calc(p, r, t):          # 参数含义不明
def process_text(text):     # 功能不具体
def convert_file(file):     # 转换成什么？
```

## 函数设计原则

### 🎯 单一职责原则

每个函数应该只做一件事，并且把它做好：

```python
# ✅ 好的设计 - 单一职责
def validate_email(email: str) -> bool:
    """验证邮箱格式是否正确"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(to: str, subject: str, body: str) -> bool:
    """发送邮件"""
    # 发送邮件的逻辑
    pass

def validate_and_send_email(to: str, subject: str, body: str) -> dict:
    """验证邮箱格式并发送邮件"""
    if not validate_email(to):
        return {"success": False, "error": "Invalid email format"}
    
    success = send_email(to, subject, body)
    return {"success": success, "message": "Email sent" if success else "Failed to send"}

# ❌ 避免的设计 - 职责混乱
def process_email(to: str, subject: str, body: str, also_validate: bool = True) -> dict:
    """既验证又发送邮件，还要处理其他逻辑"""
    # 这个函数做了太多事情
    pass
```

### 🔧 输入验证与错误处理

```python
from typing import Union, Optional
from decimal import Decimal

def calculate_loan_payment(
    principal: Union[int, float, Decimal],
    annual_rate: Union[int, float, Decimal],
    years: Union[int, float]
) -> dict:
    """
    计算贷款月供金额
    
    Args:
        principal: 贷款本金，必须大于0
        annual_rate: 年利率（百分比），例如5.5表示5.5%
        years: 贷款年限，必须大于0
        
    Returns:
        包含月供金额和其他信息的字典
        
    Raises:
        ValueError: 当输入参数无效时
    """
    # 输入验证
    try:
        principal = float(principal)
        annual_rate = float(annual_rate)
        years = float(years)
    except (TypeError, ValueError):
        raise ValueError("所有参数必须是数字类型")
    
    if principal <= 0:
        raise ValueError("贷款本金必须大于0")
    
    if annual_rate < 0:
        raise ValueError("年利率不能为负数")
    
    if years <= 0:
        raise ValueError("贷款年限必须大于0")
    
    # 计算逻辑
    monthly_rate = annual_rate / 100 / 12
    total_months = years * 12
    
    if monthly_rate == 0:
        # 无利率情况
        monthly_payment = principal / total_months
    else:
        # 有利率情况
        monthly_payment = (principal * monthly_rate * 
                          (1 + monthly_rate) ** total_months) / \
                         ((1 + monthly_rate) ** total_months - 1)
    
    total_payment = monthly_payment * total_months
    total_interest = total_payment - principal
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "principal": principal,
        "annual_rate": annual_rate,
        "years": years
    }
```

### 🎨 返回值设计

#### 一致的返回格式
```python
from typing import TypedDict, Any, Optional

class SuccessResponse(TypedDict):
    success: bool
    data: Any
    message: Optional[str]

class ErrorResponse(TypedDict):
    success: bool
    error: str
    error_code: Optional[str]

def process_data(data: list) -> Union[SuccessResponse, ErrorResponse]:
    """处理数据并返回统一格式的结果"""
    try:
        if not data:
            return {
                "success": False,
                "error": "数据不能为空",
                "error_code": "EMPTY_DATA"
            }
        
        # 处理逻辑
        processed = [item.upper() for item in data if isinstance(item, str)]
        
        return {
            "success": True,
            "data": processed,
            "message": f"成功处理了 {len(processed)} 个项目"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"处理数据时发生错误: {str(e)}",
            "error_code": "PROCESSING_ERROR"
        }
```

## 类型注解与文档

### 🏷️ 完整的类型注解

```python
from typing import List, Dict, Optional, Union, Tuple, Any
from pathlib import Path
from datetime import datetime
import pandas as pd

def analyze_sales_data(
    csv_file: Union[str, Path],
    date_column: str = "date",
    sales_column: str = "sales",
    group_by: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    分析销售数据并生成报告
    
    Args:
        csv_file: CSV文件路径
        date_column: 日期列名称，默认为"date"
        sales_column: 销售金额列名称，默认为"sales"
        group_by: 分组列名称，可选
        start_date: 开始日期，可选
        end_date: 结束日期，可选
        
    Returns:
        包含分析结果的字典：
        {
            "total_sales": float,           # 总销售额
            "average_daily_sales": float,   # 日均销售额
            "sales_trend": str,             # 销售趋势（"上升"/"下降"/"稳定"）
            "top_periods": List[Dict],      # 销售最好的时期
            "summary_stats": Dict,          # 统计摘要
            "group_analysis": Optional[Dict] # 分组分析（如果指定了group_by）
        }
        
    Raises:
        FileNotFoundError: 当CSV文件不存在时
        ValueError: 当数据格式不正确时
        KeyError: 当指定的列不存在时
    """
    # 实现逻辑...
    pass
```

### 📚 文档字符串最佳实践

```python
def generate_report(
    data: Dict[str, Any],
    template: str = "default",
    output_format: str = "pdf"
) -> Dict[str, Union[str, bytes]]:
    """
    生成格式化报告
    
    这个函数接受数据字典并使用指定模板生成报告。支持多种输出格式
    包括PDF、HTML和Word文档。
    
    Args:
        data: 要包含在报告中的数据，应包含以下键：
            - title (str): 报告标题
            - sections (List[Dict]): 报告章节，每个字典包含：
                - name (str): 章节名称
                - content (str): 章节内容
                - charts (Optional[List]): 图表数据
        template: 模板名称，可选值：
            - "default": 标准模板
            - "minimal": 简洁模板  
            - "executive": 执行摘要模板
        output_format: 输出格式，支持：
            - "pdf": PDF文档（默认）
            - "html": HTML网页
            - "docx": Word文档
            
    Returns:
        包含生成结果的字典：
        {
            "filename": str,        # 生成的文件名
            "content": bytes,       # 文件内容（二进制）
            "mime_type": str,       # MIME类型
            "size": int,           # 文件大小（字节）
            "created_at": str       # 创建时间（ISO格式）
        }
        
    Raises:
        ValueError: 
            - 数据格式不正确
            - 不支持的模板或输出格式
        TemplateNotFoundError: 模板文件不存在
        GenerationError: 报告生成过程中发生错误
        
    Example:
        >>> data = {
        ...     "title": "月度销售报告",
        ...     "sections": [
        ...         {
        ...             "name": "概览", 
        ...             "content": "本月销售总额达到100万元"
        ...         }
        ...     ]
        ... }
        >>> result = generate_report(data, template="executive")
        >>> print(f"生成报告: {result['filename']}")
        生成报告: executive_report_2024_01_15.pdf
        
    Note:
        - PDF生成需要额外安装reportlab包
        - 大型报告可能需要较长时间生成
        - 建议为复杂报告使用异步处理
    """
    # 实现逻辑...
    pass
```

## 错误处理策略

### 🛡️ 自定义异常类

```python
# common/exceptions.py
class MCPServiceError(Exception):
    """MCP服务基础异常类"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class ValidationError(MCPServiceError):
    """输入验证错误"""
    pass

class ProcessingError(MCPServiceError):
    """数据处理错误"""
    pass

class ExternalServiceError(MCPServiceError):
    """外部服务调用错误"""
    pass

class ConfigurationError(MCPServiceError):
    """配置错误"""
    pass
```

### 🎯 错误处理模式

```python
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def handle_errors(func: Callable) -> Callable:
    """统一错误处理装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        try:
            result = func(*args, **kwargs)
            return {
                "success": True,
                "data": result,
                "error": None
            }
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {e.message}")
            return {
                "success": False,
                "data": None,
                "error": {
                    "type": "validation_error",
                    "message": e.message,
                    "code": e.error_code
                }
            }
        except ProcessingError as e:
            logger.error(f"Processing error in {func.__name__}: {e.message}")
            return {
                "success": False,
                "data": None,
                "error": {
                    "type": "processing_error",
                    "message": e.message,
                    "code": e.error_code
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "data": None,
                "error": {
                    "type": "internal_error",
                    "message": "服务内部错误，请稍后重试",
                    "code": "INTERNAL_ERROR"
                }
            }
    return wrapper

# 使用示例
@handle_errors
def process_user_data(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """处理用户数据"""
    if not user_id:
        raise ValidationError("用户ID不能为空", "MISSING_USER_ID")
    
    if not isinstance(data, dict):
        raise ValidationError("数据必须是字典格式", "INVALID_DATA_FORMAT")
    
    # 处理逻辑...
    return {"processed": True, "user_id": user_id}
```

## 性能优化技巧

### ⚡ 缓存策略

```python
from functools import lru_cache, wraps
import time
from typing import Dict, Any, Callable
import hashlib
import json

# 内存缓存
@lru_cache(maxsize=128)
def expensive_calculation(n: int) -> float:
    """昂贵的计算操作，使用LRU缓存"""
    time.sleep(0.1)  # 模拟耗时操作
    return sum(i ** 2 for i in range(n))

# 带过期时间的缓存
class TimedCache:
    def __init__(self, ttl: int = 300):  # 5分钟TTL
        self.cache = {}
        self.ttl = ttl
    
    def get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        key_data = {
            "func": func_name,
            "args": args,
            "kwargs": kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        self.cache[key] = (value, time.time())

# 缓存装饰器
cache = TimedCache(ttl=300)

def cached(ttl: int = 300):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache.get_cache_key(func.__name__, args, kwargs)
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        return wrapper
    return decorator

@cached(ttl=600)  # 10分钟缓存
def fetch_external_data(api_endpoint: str) -> Dict[str, Any]:
    """获取外部API数据"""
    # 模拟API调用
    time.sleep(2)
    return {"data": f"result from {api_endpoint}"}
```

### 🔄 异步处理

```python
import asyncio
import aiohttp
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor

async def async_fetch_url(session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
    """异步获取URL内容"""
    try:
        async with session.get(url) as response:
            content = await response.text()
            return {
                "url": url,
                "status": response.status,
                "content_length": len(content),
                "success": True
            }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

async def batch_fetch_urls(urls: List[str]) -> List[Dict[str, Any]]:
    """批量异步获取多个URL"""
    async with aiohttp.ClientSession() as session:
        tasks = [async_fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results

# 在同步函数中使用异步操作
def fetch_multiple_apis(endpoints: List[str]) -> Dict[str, Any]:
    """
    并发获取多个API端点数据
    
    Args:
        endpoints: API端点URL列表
        
    Returns:
        包含所有结果的字典
    """
    if not endpoints:
        raise ValidationError("端点列表不能为空")
    
    # 运行异步操作
    results = asyncio.run(batch_fetch_urls(endpoints))
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    return {
        "total_requested": len(endpoints),
        "successful": len(successful),
        "failed": len(failed),
        "results": results,
        "summary": {
            "success_rate": len(successful) / len(endpoints) * 100,
            "total_content_length": sum(r.get("content_length", 0) for r in successful)
        }
    }
```

### 🏃‍♂️ 并行处理

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
from typing import List, Callable, Any

def cpu_intensive_task(data: List[int]) -> Dict[str, Any]:
    """CPU密集型任务"""
    result = sum(i ** 2 for i in data)
    return {
        "sum_of_squares": result,
        "count": len(data),
        "average": result / len(data) if data else 0
    }

def io_intensive_task(url: str) -> Dict[str, Any]:
    """IO密集型任务"""
    import requests
    try:
        response = requests.get(url, timeout=10)
        return {
            "url": url,
            "status_code": response.status_code,
            "content_length": len(response.content),
            "success": True
        }
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "success": False
        }

def parallel_cpu_processing(data_chunks: List[List[int]]) -> List[Dict[str, Any]]:
    """并行处理CPU密集型任务"""
    cpu_count = multiprocessing.cpu_count()
    
    with ProcessPoolExecutor(max_workers=cpu_count) as executor:
        results = list(executor.map(cpu_intensive_task, data_chunks))
    
    return results

def parallel_io_processing(urls: List[str], max_workers: int = 10) -> List[Dict[str, Any]]:
    """并行处理IO密集型任务"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(io_intensive_task, urls))
    
    return results
```

## 安全性考虑

### 🔒 输入验证与清理

```python
import re
import html
from typing import Any, Dict, List
from pathlib import Path

class SecurityValidator:
    """安全验证器"""
    
    # 危险文件扩展名
    DANGEROUS_EXTENSIONS = {'.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js'}
    
    # 允许的字符模式
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    SAFE_EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """清理字符串输入"""
        if not isinstance(text, str):
            raise ValidationError("输入必须是字符串类型")
        
        # 移除HTML标签
        text = html.escape(text)
        
        # 移除控制字符
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # 限制长度
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_file_path(file_path: str) -> str:
        """验证文件路径安全性"""
        if not isinstance(file_path, str):
            raise ValidationError("文件路径必须是字符串")
        
        # 转换为Path对象
        path = Path(file_path)
        
        # 检查路径遍历攻击
        if '..' in path.parts:
            raise ValidationError("文件路径不能包含'..'")
        
        # 检查绝对路径
        if path.is_absolute():
            raise ValidationError("不允许使用绝对路径")
        
        # 检查文件扩展名
        if path.suffix.lower() in SecurityValidator.DANGEROUS_EXTENSIONS:
            raise ValidationError(f"不允许的文件类型: {path.suffix}")
        
        # 检查文件名字符
        for part in path.parts:
            if not SecurityValidator.SAFE_FILENAME_PATTERN.match(part):
                raise ValidationError(f"文件名包含非法字符: {part}")
        
        return str(path)
    
    @staticmethod
    def validate_email(email: str) -> str:
        """验证邮箱地址"""
        if not isinstance(email, str):
            raise ValidationError("邮箱必须是字符串类型")
        
        email = email.strip().lower()
        
        if len(email) > 254:  # RFC 5321 限制
            raise ValidationError("邮箱地址过长")
        
        if not SecurityValidator.SAFE_EMAIL_PATTERN.match(email):
            raise ValidationError("邮箱格式不正确")
        
        return email

def secure_function_wrapper(func: Callable) -> Callable:
    """安全函数包装器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 验证和清理输入
        cleaned_args = []
        for arg in args:
            if isinstance(arg, str):
                cleaned_args.append(SecurityValidator.sanitize_string(arg))
            else:
                cleaned_args.append(arg)
        
        cleaned_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                cleaned_kwargs[key] = SecurityValidator.sanitize_string(value)
            else:
                cleaned_kwargs[key] = value
        
        return func(*cleaned_args, **cleaned_kwargs)
    return wrapper
```

### 🛡️ API密钥管理

```python
import os
from typing import Optional
from cryptography.fernet import Fernet

class SecureConfig:
    """安全配置管理"""
    
    def __init__(self):
        self._encryption_key = self._get_or_create_key()
        self._cipher = Fernet(self._encryption_key)
    
    def _get_or_create_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = Path("config/secret.key")
        
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            key_file.write_bytes(key)
            return key
    
    def encrypt_value(self, value: str) -> str:
        """加密值"""
        return self._cipher.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """解密值"""
        return self._cipher.decrypt(encrypted_value.encode()).decode()
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """安全地获取API密钥"""
        env_key = f"{service_name.upper()}_API_KEY"
        encrypted_key = os.getenv(env_key)
        
        if encrypted_key:
            try:
                return self.decrypt_value(encrypted_key)
            except Exception:
                return None
        
        return None

# 使用示例
secure_config = SecureConfig()

def call_external_api(service: str, endpoint: str) -> Dict[str, Any]:
    """安全地调用外部API"""
    api_key = secure_config.get_api_key(service)
    
    if not api_key:
        raise ConfigurationError(f"未找到 {service} 的API密钥")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "mcpy-cli/1.0"
    }
    
    # API调用逻辑...
    pass
```

## 测试策略

### 🧪 单元测试

```python
import pytest
from unittest.mock import Mock, patch
from your_module import calculate_loan_payment, ValidationError

class TestLoanCalculator:
    """贷款计算器测试类"""
    
    def test_valid_loan_calculation(self):
        """测试有效的贷款计算"""
        result = calculate_loan_payment(100000, 5.5, 30)
        
        assert result["success"] is True
        assert isinstance(result["monthly_payment"], float)
        assert result["monthly_payment"] > 0
        assert result["total_payment"] > result["principal"]
    
    def test_zero_interest_rate(self):
        """测试零利率情况"""
        result = calculate_loan_payment(120000, 0, 10)
        expected_monthly = 120000 / (10 * 12)
        
        assert abs(result["monthly_payment"] - expected_monthly) < 0.01
    
    @pytest.mark.parametrize("principal,rate,years,expected_error", [
        (-100000, 5.5, 30, "贷款本金必须大于0"),
        (100000, -1, 30, "年利率不能为负数"),
        (100000, 5.5, 0, "贷款年限必须大于0"),
        ("invalid", 5.5, 30, "所有参数必须是数字类型"),
    ])
    def test_invalid_inputs(self, principal, rate, years, expected_error):
        """测试无效输入"""
        with pytest.raises(ValidationError) as exc_info:
            calculate_loan_payment(principal, rate, years)
        
        assert expected_error in str(exc_info.value)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 极小金额
        result = calculate_loan_payment(1, 1, 1)
        assert result["monthly_payment"] > 0
        
        # 极高利率
        result = calculate_loan_payment(100000, 99, 1)
        assert result["total_interest"] > result["principal"]

@pytest.fixture
def mock_api_response():
    """模拟API响应的fixture"""
    return {
        "status": "success",
        "data": {"value": 123},
        "timestamp": "2024-01-01T00:00:00Z"
    }

class TestExternalAPIIntegration:
    """外部API集成测试"""
    
    @patch('requests.get')
    def test_successful_api_call(self, mock_get, mock_api_response):
        """测试成功的API调用"""
        mock_get.return_value.json.return_value = mock_api_response
        mock_get.return_value.status_code = 200
        
        result = call_external_api("test-service", "/test-endpoint")
        
        assert result["success"] is True
        assert "data" in result
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_api_failure(self, mock_get):
        """测试API调用失败"""
        mock_get.side_effect = Exception("Network error")
        
        result = call_external_api("test-service", "/test-endpoint")
        
        assert result["success"] is False
        assert "error" in result
```

### 🔄 集成测试

```python
import pytest
from fastapi.testclient import TestClient
from your_app import create_mcp_application

@pytest.fixture
def test_app():
    """创建测试应用"""
    app = create_mcp_application(
        source_path_str="tests/fixtures/test_tools",
        mode="composed"
    )
    return TestClient(app)

class TestMCPIntegration:
    """MCP集成测试"""
    
    def test_service_health(self, test_app):
        """测试服务健康检查"""
        response = test_app.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_tool_discovery(self, test_app):
        """测试工具发现"""
        response = test_app.post("/mcp", json={
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "tools" in data["result"]
        assert len(data["result"]["tools"]) > 0
    
    def test_tool_execution(self, test_app):
        """测试工具执行"""
        response = test_app.post("/mcp", json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "add_numbers",
                "arguments": {"a": 5, "b": 3}
            },
            "id": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["content"][0]["text"] == "8"
```

## 部署与运维

### 🐳 Docker化

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-service:
    build: .
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=INFO
      - MCP_SERVER_NAME=production-service
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

### 📊 监控与日志

```python
# config/logging.py
import logging.config
import json
from datetime import datetime

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

def setup_logging():
    """设置日志配置"""
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(LOGGING_CONFIG)
```

### 🔍 性能监控

```python
import time
import psutil
from functools import wraps
from typing import Dict, Any

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_execution_time(self, func_name: str):
        """跟踪函数执行时间装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                except Exception as e:
                    status = "error"
                    raise
                finally:
                    execution_time = time.time() - start_time
                    self._record_metric(func_name, execution_time, status)
                return result
            return wrapper
        return decorator
    
    def _record_metric(self, func_name: str, execution_time: float, status: str):
        """记录性能指标"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                "total_calls": 0,
                "total_time": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_time": 0,
                "max_time": 0,
                "min_time": float('inf')
            }
        
        metric = self.metrics[func_name]
        metric["total_calls"] += 1
        metric["total_time"] += execution_time
        metric[f"{status}_count"] += 1
        metric["avg_time"] = metric["total_time"] / metric["total_calls"]
        metric["max_time"] = max(metric["max_time"], execution_time)
        metric["min_time"] = min(metric["min_time"], execution_time)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "process_count": len(psutil.pids()),
            "timestamp": time.time()
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "function_metrics": self.metrics,
            "system_metrics": self.get_system_metrics(),
            "uptime": time.time() - self.start_time if hasattr(self, 'start_time') else 0
        }

# 全局监控器实例
monitor = PerformanceMonitor()

# 使用示例
@monitor.track_execution_time("data_processing")
def process_large_dataset(data: List[Dict]) -> Dict[str, Any]:
    """处理大型数据集"""
    # 处理逻辑...
    pass
```

## 常见陷阱与避免方法

### ⚠️ 常见错误

#### 1. 内存泄漏
```python
# ❌ 错误：全局变量累积数据
global_cache = {}

def process_data(data):
    global_cache[len(global_cache)] = data  # 不断累积，永不清理
    return len(data)

# ✅ 正确：使用有限制的缓存
from functools import lru_cache

@lru_cache(maxsize=100)  # 限制缓存大小
def process_data(data_hash):
    return expensive_operation(data_hash)
```

#### 2. 阻塞操作
```python
# ❌ 错误：同步阻塞操作
def fetch_all_data(urls):
    results = []
    for url in urls:
        response = requests.get(url)  # 串行阻塞
        results.append(response.json())
    return results

# ✅ 正确：异步非阻塞操作
async def fetch_all_data(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_single_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

#### 3. 不当的异常处理
```python
# ❌ 错误：吞掉所有异常
def risky_operation():
    try:
        # 危险操作
        pass
    except:  # 捕获所有异常但不处理
        pass

# ✅ 正确：具体异常处理
def risky_operation():
    try:
        # 危险操作
        pass
    except SpecificException as e:
        logger.error(f"具体错误: {e}")
        raise  # 重新抛出以便上层处理
    except Exception as e:
        logger.error(f"未预期错误: {e}")
        raise MCPServiceError("操作失败") from e
```

### 💡 最佳实践总结

1. **代码质量**
   - 使用类型注解和详细文档
   - 实施全面的错误处理
   - 编写充分的测试用例
   - 遵循PEP 8编码规范

2. **性能优化**
   - 合理使用缓存机制
   - 异步处理IO密集型任务
   - 并行处理CPU密集型任务
   - 监控和优化性能瓶颈

3. **安全性**
   - 验证和清理所有输入
   - 安全地管理敏感信息
   - 使用HTTPS和适当的认证
   - 定期更新依赖包

4. **运维友好**
   - 完善的日志记录
   - 健康检查端点
   - 性能监控指标
   - 容器化部署

5. **团队协作**
   - 清晰的项目结构
   - 详细的文档说明
   - 一致的编码风格
   - 自动化测试和部署

遵循这些最佳实践，您将能够构建出高质量、可维护、高性能的MCP服务！ 