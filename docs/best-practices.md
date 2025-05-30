# 📝 MCP 兼容的 Python 函数设计最佳实践

本指南专注于如何设计和组织 Python 函数以及文件结构，使其完全兼容 MCP-CLI 的自动函数发现和服务生成功能。

## 📋 目录

- [MCP 函数设计要求](#mcp-函数设计要求)
- [类型注解与文档规范](#类型注解与文档规范)
- [文件组织与路由](#文件组织与路由)
- [项目结构最佳实践](#项目结构最佳实践)
- [函数命名与发现](#函数命名与发现)
- [常见问题与解决方案](#常见问题与解决方案)

## MCP 函数设计要求

### 🎯 核心要求概览

MCP-CLI 对 Python 函数有特定的技术要求，确保函数能够被正确发现、验证和转换为 MCP 工具：

#### ✅ 必需要求
1. **类型注解**: 所有参数和返回值必须有类型注解
2. **文档字符串**: 必须提供详细的 docstring
3. **函数可见性**: 函数名不能以下划线开头（私有函数会被跳过）
4. **参数限制**: 不支持 `*args` 和 `**kwargs`

#### ❌ 不支持的模式
```python
# ❌ 错误：缺少类型注解
def bad_function(a, b):
    return a + b

# ❌ 错误：使用 *args
def bad_function(a: int, *args) -> int:
    return sum([a] + list(args))

# ❌ 错误：使用 **kwargs
def bad_function(a: int, **kwargs) -> int:
    return a + kwargs.get('b', 0)

# ❌ 错误：私有函数（以 _ 开头）
def _private_function(a: int, b: int) -> int:
    return a + b

# ❌ 错误：缺少 docstring
def undocumented_function(a: int, b: int) -> int:
    return a + b
```

#### ✅ 正确的 MCP 兼容函数
```python
def add_numbers(a: int, b: int) -> int:
    """
    Add two integers together.
    
    Args:
        a: The first integer
        b: The second integer
        
    Returns:
        The sum of a and b
    """
    return a + b

def process_text(text: str, uppercase: bool = False) -> str:
    """
    Process text with optional uppercase conversion.
    
    Args:
        text: The input text to process
        uppercase: Whether to convert to uppercase
        
    Returns:
        The processed text
    """
    return text.upper() if uppercase else text.lower()
```

### 🔍 函数验证过程

MCP-CLI 在发现函数时会执行以下验证步骤：

1. **模块级过滤**: 只包含当前模块定义的函数（跳过导入的函数）
2. **可见性检查**: 跳过以下划线开头的私有函数
3. **类型注解验证**: 检查所有参数和返回值的类型注解
4. **参数类型检查**: 确保不使用 `*args` 或 `**kwargs`
5. **文档字符串检查**: 验证是否提供了 docstring

## 类型注解与文档规范

### 📚 支持的类型注解

#### 基础类型
```python
from typing import List, Dict, Optional, Union

def handle_basic_types(
    text: str,
    number: int,
    decimal: float,
    flag: bool
) -> str:
    """Handle basic Python types."""
    return f"{text}: {number}, {decimal}, {flag}"
```

#### 复合类型
```python
from typing import List, Dict, Optional, Union

def handle_complex_types(
    items: List[str],
    mapping: Dict[str, int],
    optional_value: Optional[str] = None,
    union_value: Union[str, int] = "default"
) -> Dict[str, any]:
    """
    Handle complex type annotations.
    
    Args:
        items: List of string items
        mapping: Dictionary mapping strings to integers
        optional_value: Optional string parameter
        union_value: Either string or integer value
        
    Returns:
        Dictionary containing processed results
    """
    return {
        "items_count": len(items),
        "mapping_keys": list(mapping.keys()),
        "has_optional": optional_value is not None,
        "union_type": type(union_value).__name__
    }
```

#### Pydantic 模型支持
```python
from pydantic import BaseModel
from typing import List

class UserData(BaseModel):
    name: str
    age: int
    email: str

def process_user_data(user: UserData) -> Dict[str, str]:
    """
    Process user data using Pydantic models.
    
    Args:
        user: User data model with name, age, and email
        
    Returns:
        Dictionary with processed user information
    """
    return {
        "greeting": f"Hello {user.name}",
        "age_group": "adult" if user.age >= 18 else "minor",
        "domain": user.email.split('@')[1]
    }
```

### 📝 文档字符串格式

MCP-CLI 推荐使用 Google 风格的 docstring，但也支持其他格式：

#### Google 风格（推荐）
```python
def calculate_area(length: float, width: float) -> float:
    """
    Calculate the area of a rectangle.
    
    Args:
        length: The length of the rectangle in units
        width: The width of the rectangle in units
        
    Returns:
        The area of the rectangle in square units
        
    Raises:
        ValueError: If length or width is negative
    """
    if length < 0 or width < 0:
        raise ValueError("Length and width must be non-negative")
    return length * width
```

#### Sphinx 风格
```python
def divide_numbers(dividend: float, divisor: float) -> float:
    """
    Divide two numbers.
    
    :param dividend: The number to be divided
    :param divisor: The number to divide by
    :return: The result of division
    :raises ZeroDivisionError: If divisor is zero
    """
    if divisor == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return dividend / divisor
```

#### NumPy 风格
```python
def compute_statistics(data: List[float]) -> Dict[str, float]:
    """
    Compute basic statistics for a list of numbers.
    
    Parameters
    ----------
    data : List[float]
        List of numerical values
        
    Returns
    -------
    Dict[str, float]
        Dictionary containing mean, median, and standard deviation
    """
    import statistics
    return {
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "stdev": statistics.stdev(data) if len(data) > 1 else 0.0
    }
```

## 文件组织与路由

### 🏗️ 架构模式对文件组织的影响

#### Composed 模式（默认）
在 Composed 模式下，所有函数通过单一入口访问，函数名会添加文件名前缀：

```
my_tools/
├── math_utils.py      # 函数: add, multiply
├── text_utils.py      # 函数: format_text, count_words
└── data_utils.py      # 函数: parse_csv, validate_json

# 生成的工具名：
# tool_math_utils_add
# tool_math_utils_multiply  
# tool_text_utils_format_text
# tool_text_utils_count_words
# tool_data_utils_parse_csv
# tool_data_utils_validate_json

# 访问端点：
# http://localhost:8080/mcp-server/mcp
```

**最佳实践**：
- 使用描述性的文件名，避免冲突
- 考虑函数的逻辑分组
- 文件名会成为函数名的一部分，保持简洁

```python
# math_utils.py
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract second number from first."""
    return a - b
```

#### Routed 模式
在 Routed 模式下，每个文件创建独立的服务端点：

```
my_tools/
├── math/
│   ├── basic.py       # 端点: /math/basic
│   └── advanced.py    # 端点: /math/advanced
├── text/
│   ├── processing.py  # 端点: /text/processing  
│   └── analysis.py    # 端点: /text/analysis
└── utils.py           # 端点: /utils

# 访问端点：
# http://localhost:8080/math/basic/mcp
# http://localhost:8080/math/advanced/mcp
# http://localhost:8080/text/processing/mcp
# http://localhost:8080/text/analysis/mcp
# http://localhost:8080/utils/mcp
```

**最佳实践**：
- 目录结构直接映射到 URL 路径
- 每个文件应该有清晰的职责边界
- 函数名保持原样，无自动前缀

```python
# math/basic.py
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
```

## 项目结构最佳实践

### 📁 小型项目（< 10个工具）

```
my_mcp_service/
├── tools.py              # 所有工具函数
├── requirements.txt       # 依赖管理
├── .env                  # 环境变量
├── README.md             # 项目说明
└── tests/
    ├── test_tools.py     # 测试文件
    └── __init__.py

# 启动命令（Composed 模式）
mcpy-cli run --source-path tools.py --mode composed
```

**工具函数示例**：
```python
# tools.py
from typing import List, Dict

def calculate_sum(numbers: List[float]) -> float:
    """
    Calculate the sum of a list of numbers.
    
    Args:
        numbers: List of numbers to sum
        
    Returns:
        The sum of all numbers
    """
    return sum(numbers)

def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: The amount to format
        currency: The currency code (default: USD)
        
    Returns:
        Formatted currency string
    """
    return f"{amount:.2f} {currency}"
```

### 📁 中型项目（10-30个工具）

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
│   ├── validators.py     # 输入验证（非工具函数）
│   ├── exceptions.py     # 自定义异常
│   └── helpers.py        # 辅助函数（非工具函数）
├── requirements.txt
├── .env.example
└── README.md

# 启动命令
# Composed 模式：
mcpy-cli run --source-path tools/ --mode composed

# Routed 模式：
mcpy-cli run --source-path tools/ --mode routed
```

**模块组织示例**：
```python
# tools/math_utils.py
from typing import List
import math

def calculate_average(numbers: List[float]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers
        
    Returns:
        The average value
    """
    return sum(numbers) / len(numbers) if numbers else 0.0

def calculate_factorial(n: int) -> int:
    """
    Calculate factorial of a number.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    return math.factorial(n)
```

### 📁 大型项目（> 30个工具）

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
│   ├── validators.py     # 输入验证
│   ├── exceptions.py     # 异常定义
│   └── helpers.py        # 辅助函数
├── config/
│   ├── __init__.py
│   ├── settings.py       # 设置管理
│   └── constants.py      # 常量定义
├── tests/
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── e2e/            # 端到端测试
├── requirements.txt
├── .env.example
└── README.md

# 推荐使用 Routed 模式：
mcpy-cli run --source-path services/ --mode routed
```

**服务模块示例**：
```python
# services/text/processing.py
from typing import List, Dict

def clean_text(text: str, remove_punctuation: bool = True) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: The input text to clean
        remove_punctuation: Whether to remove punctuation marks
        
    Returns:
        Cleaned text
    """
    import re
    import string
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    if remove_punctuation:
        text = text.translate(str.maketrans('', '', string.punctuation))
    
    return text

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Input text for keyword extraction
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of extracted keywords
    """
    # Simple keyword extraction (word frequency)
    words = text.lower().split()
    word_freq = {}
    
    for word in words:
        if len(word) > 3:  # Skip short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]
```

## 函数命名与发现

### 🔍 函数发现规则

MCP-CLI 使用以下规则来发现和过滤函数：

1. **模块检查**: 只包含在当前模块中定义的函数
2. **可见性过滤**: 跳过以下划线开头的函数（除了特殊方法 `__method__`）
3. **类型检查**: 确保函数是可调用对象

```python
# ✅ 会被发现的函数
def public_function() -> str:
    """This function will be discovered."""
    return "public"

def another_public_function() -> str:
    """This function will also be discovered."""  
    return "also public"

# ❌ 不会被发现的函数
def _private_function() -> str:
    """This private function will be skipped."""
    return "private"

def __special_method__(self) -> str:
    """Special methods are skipped."""
    return "special"

# ✅ 从其他模块导入的函数不会被包含
from math import sqrt  # sqrt 不会被注册为工具
```

### 📝 命名最佳实践

#### Composed 模式命名策略
```python
# 文件：math_operations.py

def add_integers(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

def multiply_floats(a: float, b: float) -> float:
    """Multiply two floating point numbers."""
    return a * b

# 生成的工具名：
# tool_math_operations_add_integers
# tool_math_operations_multiply_floats
```

**建议**：
- 使用描述性的函数名
- 避免过长的函数名（会导致工具名过长）
- 考虑函数名和文件名的组合效果

#### Routed 模式命名策略
```python
# 文件：math/basic.py

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b

# 生成的工具名保持原样：
# add
# subtract
# 访问路径：/math/basic/mcp
```

**建议**：
- 在模块内保持函数名的一致性
- 函数名应该清晰描述其功能
- 避免在同一模块内使用相似的函数名

### 🎯 特定函数选择

可以使用 `--functions` 参数来指定要暴露的特定函数：

```bash
# 只暴露特定函数
mcpy-cli run --source-path tools.py --functions "add_numbers,multiply_numbers"

# 在多文件项目中指定函数
mcpy-cli run --source-path tools/ --functions "calculate_sum,format_text,process_data"
```

## 常见问题与解决方案

### ❓ 常见问题排查

#### 1. 函数未被发现

**问题**: 函数明明存在，但没有被 MCP-CLI 发现

**可能原因**：
- 函数缺少类型注解
- 函数名以下划线开头
- 函数在另一个模块中定义（通过 import 导入）
- 文件中有语法错误

**解决方案**：
```python
# ❌ 问题示例
def problematic_function(a, b):  # 缺少类型注解
    return a + b

def _another_function(a: int, b: int) -> int:  # 私有函数
    return a + b

from math import factorial  # 导入的函数不会被发现

# ✅ 正确示例
def working_function(a: int, b: int) -> int:
    """
    Add two integers.
    
    Args:
        a: First integer
        b: Second integer
        
    Returns:
        Sum of a and b
    """
    return a + b
```

#### 2. 类型注解错误

**问题**: 类型注解导致运行时错误

**解决方案**：
```python
# ✅ 正确的类型注解
from typing import List, Dict, Optional, Union
from datetime import datetime

def process_data(
    items: List[str],
    config: Dict[str, any],
    timestamp: Optional[datetime] = None
) -> Dict[str, Union[str, int]]:
    """Process data with proper type annotations."""
    if timestamp is None:
        timestamp = datetime.now()
    
    return {
        "count": len(items),
        "first_item": items[0] if items else "",
        "processed_at": timestamp.isoformat()
    }
```

#### 3. 文档字符串格式问题

**问题**: 缺少文档字符串或格式不规范

**解决方案**：
```python
# ✅ 完整的文档字符串示例
def comprehensive_function(
    data: List[float],
    threshold: float = 0.5,
    normalize: bool = True
) -> Dict[str, any]:
    """
    Process numerical data with filtering and optional normalization.
    
    This function filters data based on a threshold value and optionally
    normalizes the results to a 0-1 range.
    
    Args:
        data: List of numerical values to process
        threshold: Minimum value to include in results (default: 0.5)
        normalize: Whether to normalize results to 0-1 range (default: True)
        
    Returns:
        Dictionary containing:
            - filtered_data: List of values above threshold
            - statistics: Basic statistics (mean, max, min)
            - normalized: Normalized values (if normalize=True)
            
    Raises:
        ValueError: If data is empty or contains non-numeric values
        
    Example:
        >>> result = comprehensive_function([1.0, 2.0, 0.3, 1.5], threshold=0.5)
        >>> print(result['statistics']['mean'])
        1.45
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    # Filter data
    filtered_data = [x for x in data if x >= threshold]
    
    if not filtered_data:
        raise ValueError("No data points above threshold")
    
    # Calculate statistics
    stats = {
        "mean": sum(filtered_data) / len(filtered_data),
        "max": max(filtered_data),
        "min": min(filtered_data)
    }
    
    result = {
        "filtered_data": filtered_data,
        "statistics": stats
    }
    
    # Optional normalization
    if normalize and stats["max"] > stats["min"]:
        range_val = stats["max"] - stats["min"]
        normalized = [(x - stats["min"]) / range_val for x in filtered_data]
        result["normalized"] = normalized
    
    return result
```

#### 4. 架构模式选择困惑

**Composed vs Routed 选择指南**：

**选择 Composed 模式当**：
- 工具数量 < 30 个
- 需要统一的 API 入口
- 工具之间有逻辑关联
- 简化部署和管理
- 团队规模较小

**选择 Routed 模式当**：
- 工具数量 > 30 个
- 需要模块化管理
- 不同团队负责不同模块
- 需要独立扩展特定模块
- 企业级应用需求

#### 5. 性能优化建议

**函数设计优化**：
```python
# ✅ 高效的函数设计
from functools import lru_cache
from typing import List

@lru_cache(maxsize=128)
def expensive_calculation(value: int) -> float:
    """
    Perform expensive calculation with caching.
    
    Args:
        value: Input value for calculation
        
    Returns:
        Calculated result
    """
    # 模拟复杂计算
    import time
    time.sleep(0.1)  # 模拟耗时操作
    return value ** 2 * 3.14159

def batch_process(items: List[str], batch_size: int = 100) -> List[str]:
    """
    Process items in batches for better performance.
    
    Args:
        items: List of items to process
        batch_size: Number of items to process at once
        
    Returns:
        List of processed items
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        # 批量处理逻辑
        processed_batch = [item.upper() for item in batch]
        results.extend(processed_batch)
    return results
```

### 🔧 调试技巧

#### 启用详细日志
```bash
# 启用 DEBUG 级别日志查看详细的函数发现过程
mcpy-cli run --source-path tools/ --log-level DEBUG
```

#### 验证函数发现
```bash
# 列出所有发现的函数（不启动服务）
mcpy-cli run --source-path tools/ --help

# 检查特定函数
mcpy-cli run --source-path tools/ --functions "specific_function" --log-level DEBUG
```

#### 测试工具调用
```bash
# 启动服务后，访问工具列表
curl http://localhost:8080/mcp-server/mcp/list_tools

# 调用特定工具（Composed 模式）
curl -X POST http://localhost:8080/mcp-server/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tool_math_utils_add", "params": {"a": 5, "b": 3}, "id": 1}'
```

## 🚀 传输协议选择最佳实践

### 默认传输协议（推荐）

**始终优先选择默认的 Streamable HTTP 传输协议**：

```bash
# ✅ 推荐：使用默认传输协议
mcpy-cli run --source-path tools/
```

**优势**：
- 🔧 **单端点架构**: 简化部署和调试
- ☁️ **云环境兼容**: 完全兼容 Knative、Istio 等云原生环境
- 🚀 **现代化设计**: 支持最新的 HTTP 流式传输标准
- 🔒 **更好的安全性**: 更好的网络安全策略兼容性

### Legacy SSE 传输协议（不推荐）

**仅在以下情况下使用 `--legacy-sse`**：

```bash
# ⚠️ 仅用于向后兼容
mcpy-cli run --source-path tools/ --legacy-sse
```

**使用场景**：
- 🔙 **向后兼容**: 现有系统依赖 SSE 传输模式
- 🔄 **渐进迁移**: 从旧版本逐步迁移到新传输协议

**重要限制**：
- ❌ **已弃用**: 此选项在未来版本中将被移除
- ☁️ **云环境问题**: 在 Knative、Istio 等环境中存在已知问题
- 🛠️ **双端点复杂性**: 需要管理两个独立的 HTTP 端点

### 迁移建议

#### 新项目
```bash
# ✅ 新项目直接使用默认传输协议
mcpy-cli run --source-path my_new_project/
```

#### 现有项目迁移
```bash
# 步骤 1: 测试默认传输协议
mcpy-cli run --source-path existing_project/ --port 8081

# 步骤 2: 验证功能正常后，更新部署配置
# 移除 --legacy-sse 参数

# 步骤 3: 更新客户端连接配置（如果需要）
```

#### 云环境部署
```bash
# ✅ 云环境中始终使用默认传输协议
mcpy-cli run --source-path tools/ --host 0.0.0.0 --port 8080
```

### 传输协议对比

| 特性 | 默认 Streamable HTTP | Legacy SSE |
|------|---------------------|------------|
| 架构 | 单端点 | 双端点 |
| 云兼容性 | ✅ 完全兼容 | ❌ 存在问题 |
| 维护状态 | ✅ 活跃维护 | ⚠️ 已弃用 |
| 部署复杂度 | 🟢 简单 | 🟡 复杂 |
| 推荐使用 | ✅ 是 | ❌ 否 |

---

通过遵循这些最佳实践，您可以确保 Python 函数完全兼容 MCP-CLI 的自动发现和服务生成功能，并选择最适合的传输协议，创建高质量、可维护的 MCP 服务。