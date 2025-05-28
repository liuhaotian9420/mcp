
# 📚 MCP 服务快速入门指南

从零开始改造出你的第一个 **MCP 服务**，涵盖环境准备、代码编写、服务启动、测试以及进阶配置等内容。

---

## 🛠️ 环境准备

### ✅ 系统要求

- **Python**: 3.10 或更高版本
---

### 📦 安装 mcpy-cli

#### 方法一：使用 pip 安装

```bash
pip install mcpy-cli
```

#### 方法二：使用 uv 安装（推荐）

```bash
# 安装 uv
pip install uv

# 使用 uv 安装
uv pip install mcpy-cli
```

---

### 🧪 验证安装

成功安装后，运行以下命令验证：

```bash
mcpy-cli --version
mcpy-cli --help
```

---

## 🧱 创建第一个服务

### 📁 步骤 1: 创建项目目录

```bash
mkdir my-first-mcp-service
cd my-first-mcp-service
```

---

### 📄 步骤 2: 编写工具函数

创建 `tools.py` 文件，编写几个示例工具函数：

```python
def add_numbers(a: float, b: float) -> float:
    """
    计算两个数的和
  
    Args:
        a: 第一个数字
        b: 第二个数字
      
    Returns:
        两个数字的和
    """
    return a + b

def multiply_numbers(a: float, b: float) -> float:
    """
    计算两个数的乘积
  
    Args:
        a: 第一个数字
        b: 第二个数字
      
    Returns:
        两个数字的乘积
    """
    return a * b

def calculate_area(length: float, width: float) -> dict:
    """
    计算矩形的面积和周长
  
    Args:
        length: 矩形的长度
        width: 矩形的宽度
      
    Returns:
        包含面积和周长的字典
    """
    area = length * width
    perimeter = 2 * (length + width)
  
    return {
        "area": area,
        "perimeter": perimeter,
        "dimensions": {
            "length": length,
            "width": width
        }
    }

def greet_user(name: str, language: str = "chinese") -> str:
    """
    用指定语言问候用户
  
    Args:
        name: 用户姓名
        language: 问候语言，支持 'chinese', 'english', 'spanish'
      
    Returns:
        问候语
    """
    greetings = {
        "chinese": f"你好，{name}！",
        "english": f"Hello, {name}!",
        "spanish": f"¡Hola, {name}!"
    }
  
    return greetings.get(language.lower(), f"Hello, {name}!")
```

---

### 🚀 步骤 3: 启动服务

#### 使用 MCP 服务运行器启动

```bash
mcpy-cli run --source-path tools.py --port 8080
```

#### 使用 uv 启动（推荐）

```bash
uvx mcpy-cli run --source-path tools.py --port 8080
```

你将看到如下输出：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

🎉 恭喜！你的第一个 MCP 服务已经成功运行了！

---

## 🧪 查看服务效果

### 🔎 使用 MCP Inspector 查看效果（推荐）

- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) 是一个主流的测试 MCP 服务器的工具

- 可以通过如下的方式安装（需要本地有 Node.js)
```bash
npx @modelcontextprotocol/inspector node build/index.js
```
- 运行命令后点击命令行内的链接就可以打开窗口了，具体的操作指南详见 [MCP 官方文档](https://modelcontextprotocol.io/docs/tools/inspector)


### 🌐 使用本地客户端（如 CherryStudio）测试

以 CherryStudio 为例，
1. 点击【设置】-【MCP 服务器】-【添加服务器】
2. 在【类型】 处选择 【可流式传输的HTTP】
3. URL 处填写服务部署的地址，具体地址的格式见[MCP 服务器地址](docs/architecture-modes.md)
4. 点击右上角的【保存】，等待服务器启动和加载，没有报错即可
5. 
---

### 🧪 使用 Python 客户端测试

创建 `test_client.py` 文件：

```python
import requests
import json

def call_mcp_tool(tool_name: str, parameters: dict):
    """调用 MCP 工具"""
    url = "http://localhost:8080/mcp-server/mcp"
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": parameters
        },
        "id": 1
    }
  
    response = requests.post(url, json=payload)
    return response.json()

# 测试数学运算
def test_math_operations():
    print("=== 测试数学运算 ===")
  
    # 加法
    result = call_mcp_tool("add_numbers", {"a": 15, "b": 25})
    print(f"15 + 25 = {result}")
  
    # 乘法
    result = call_mcp_tool("multiply_numbers", {"a": 6, "b": 7})
    print(f"6 × 7 = {result}")
  
    # 面积计算
    result = call_mcp_tool("calculate_area", {"length": 10, "width": 5})
    print(f"矩形面积和周长: {result}")

# 测试问候功能
def test_greetings():
    print("\n=== 测试问候功能 ===")
  
    # 中文
    result = call_mcp_tool("greet_user", {"name": "张三", "language": "chinese"})
    print(f"中文问候: {result}")
  
    # 英文
    result = call_mcp_tool("greet_user", {"name": "John", "language": "english"})
    print(f"英文问候: {result}")
  
    # 西班牙语
    result = call_mcp_tool("greet_user", {"name": "Maria", "language": "spanish"})
    print(f"西班牙语问候: {result}")

if __name__ == "__main__":
    test_math_operations()
    test_greetings()
```

运行测试脚本：

```bash
python test_client.py
```

---

### 📡 使用 curl 测试

#### 获取工具列表

```bash
curl -X POST http://localhost:8080/mcp-server/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

#### 调用加法工具

```bash
curl -X POST http://localhost:8080/mcp-server/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_numbers",
      "arguments": {"a": 10, "b": 20}
    },
    "id": 1
  }'
```

---

## 🧩 进阶配置

### 📁 多文件结构

一个更复杂的项目结构如下：

```
my-advanced-service/
├── math_tools.py      # 数学工具
├── text_tools.py      # 文本工具
├── data_tools.py      # 数据工具
└── config.py          # 配置文件
```

#### math_tools.py 示例

```python
def calculate_factorial(n: int) -> int:
    """计算阶乘"""
    if n < 0:
        raise ValueError("阶乘不支持负数")
    if n == 0 or n == 1:
        return 1
    return n * calculate_factorial(n - 1)

def fibonacci_sequence(n: int) -> list:
    """生成斐波那契数列"""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
  
    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence
```

#### text_tools.py 示例

```python
def count_words(text: str) -> dict:
    """统计文本词数"""
    words = text.split()
    word_count = {}
  
    for word in words:
        word = word.lower().strip('.,!?;:"')
        word_count[word] = word_count.get(word, 0) + 1
  
    return {
        "total_words": len(words),
        "unique_words": len(word_count),
        "word_frequency": word_count
    }

def reverse_text(text: str) -> str:
    """反转文本"""
    return text[::-1]
```

#### data_tools.py 示例

```python
from typing import List, Dict, Any

def process_sales_data(sales_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """处理销售数据"""
    if not sales_data:
        return {"error": "没有销售数据"}
  
    total_sales = sum(item.get("amount", 0) for item in sales_data)
    avg_sales = total_sales / len(sales_data)
  
    return {
        "total_sales": total_sales,
        "average_sales": avg_sales,
        "transaction_count": len(sales_data),
        "summary": f"总销售额: {total_sales}, 平均销售额: {avg_sales:.2f}"
    }
```

---

### 🔄 使用不同架构模式

#### Composed 模式（默认）

```bash
mcpy-cli run --source-path . --mode composed --port 8080
```

#### Routed 模式

```bash
mcpy-cli run --source-path . --mode routed --port 8080
```

---

### 📄 环境变量配置

创建 `.env` 文件：

```env
# 服务配置
HOST=0.0.0.0
PORT=8080
MCP_SERVER_NAME=my-advanced-service

# 日志配置
LOG_LEVEL=INFO

# 安全配置
CORS_ORIGINS=*
```

---

### 🚀 高级启动选项

```bash
mcpy-cli run \
  --source-path . \
  --port 8080 \
  --host 0.0.0.0 \
  --mcp-name "AdvancedMCPService" \
  --mode composed
```

---

## 🤔 常见问题与解决方案

### Q1: 服务启动失败，提示端口被占用

**原因**：端口 8080 被其他程序占用。

**解决方法**：

使用不同端口：

```bash
mcpy-cli run --source-path tools.py --port 9000
```

或者查找并终止占用端口的进程：

**Windows**：

```bash
netstat -ano | findstr :8080
taskkill /PID <进程ID> /F
```

**Linux/macOS**：

```bash
lsof -ti:8080 | xargs kill -9
```

---

### Q2: 函数没有被发现

**可能原因**：

- 函数缺少类型注解
- 函数缺少文档字符串
- 函数名以下划线开头

**解决方法**：

✅ 正确的函数定义：

```python
def my_function(param: str) -> str:
    """函数描述"""
    return param
```

❌ 错误的函数定义：

```python
def _private_function():  # 以下划线开头
    pass

def no_annotation_function(param):  # 缺少类型注解
    return param
```

---

### Q3: 类型验证错误

**解决方法**：

确保函数参数和返回值有清晰的类型注解：

```python
from typing import List, Dict, Optional, Union

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Union[int, str]]:
    """处理数据并返回结果"""
    # 实现逻辑
    pass
```

---

### Q4: 如何调试函数执行

**方法一：添加日志**

```python
import logging

logger = logging.getLogger(__name__)

def my_function(data: str) -> str:
    """带调试的函数"""
    logger.info(f"Processing data: {data}")
    result = data.upper()
    logger.info(f"Result: {result}")
    return result
```

**方法二：使用异常处理**

```python
def safe_function(data: str) -> dict:
    """安全的函数执行"""
    try:
        result = risky_operation(data)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

### Q5: 如何部署到生产环境

1. 打包服务：

```bash
mcpy-cli package --source-path . --output my-service.zip
```

2. 在目标服务器解压并安装依赖：

```bash
unzip my-service.zip
cd my-service/project
pip install -r requirements.txt
```

3. 启动生产服务：

```bash
python main.py
```

---

## 🧭 下一步

你现在已成功创建并运行了第一个 MCP 服务！接下来你可以：

- 📖 学习更多：查看 [架构设计指南](architecture.md) 了解系统原理
- 🛠️ 最佳实践：阅读 [最佳实践指南](best-practices.md) 优化代码质量
- 🔧 高级配置：探索 [配置管理](configuration/) 了解更多选项
- 🚀 生产部署：查看 [部署指南](deployment/) 学习生产环境部署
- 🧪 示例项目：参考 [示例项目](examples/) 获取更多灵感

---

## 📢 帮助与支持

如果你有任何问题，可以：

- 查看 [常见问题](best-practices/faq.md)
- 提交 [Issue](https://github.com/your-project/issues)

---

祝你开发愉快！🚀