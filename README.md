以下是优化后的版本，去除了面向开发者的技术细节，保留了用户友好的说明和操作指南：


# 🚀 轻松构建与部署 MCP 服务：`mcp-modelservice-sdk` 实战指南

*[English Version](README.en.md)*

欢迎使用 `mcp-modelservice-sdk`！本指南将帮助您快速上手，通过简单的步骤创建、运行、转换和部署自己的 MCP (模型上下文协议) 服务。


## 什么是 `mcp-modelservice-sdk`？

这是一个专为简化 MCP 服务开发而设计的工具包。它能帮助您：
- 📦 **快速打包**：将一个或是多个 Python 函数或脚本转换为标准 MCP 服务
- 🚀 **一键部署**：通过命令行快速启动或发布服务
- 🔄 **自动路由**：根据文件结构自动生成服务接口
- 🌐 **跨平台兼容**：支持多种传输协议和部署环境


## 🔥 快速开始

### 1. 环境要求：

Python >= 3.10, 且安装了 FastMCP, 推荐安装 uv

```bash
# 使用 pip 下载
pip install mcp-modelservice-sdk

# 使用 uv (如已安装)
uv pip install mcp-modelservice-sdk

# 使用 uv (未安装)
pip install uv
uv pip install mcp-modelservice-sdk

```


### 2. 快速启动

使用内置示例快速体验：

```bash
# 启动示例服务
mcp-modelservice run --source-path path-to-your-file-or-directory --port 8080

# 服务启动后，访问测试页面：
# http://localhost:8080/mcp-server/mcp
```

或者如果你安装了 uv

```bash
# 启动示例服务
uvx --from mcp-modelservice-sdk mcp-modelservice --source-path path-to-your-file-or-directory run  --port 8080

# 服务启动后，访问测试页面：
# http://localhost:8080/mcp-server/mcp
```


### 3. 使用您自己的代码

将您的 Python 函数转换为 MCP 服务：

```python
# 创建 my_tools.py 文件
def add(a: float, b: float) -> float:
    """两个数相加"""
    return a + b

def multiply(a: float, b: float) -> float:
    """两个数相乘"""
    return a * b
```

然后启动服务：

```bash
 mcp-modelservice run --source-path my_tools.py --port 9000
```

## 📖 使用指南

### 🔬 两大核心模式

**1. 本地运行模式 (run)**

- 使用 `mcp-modelservice run` 命令可以在本地将多个 Python 文件中的函数部署为若干个指定端口的 MCP 服务

**2. 打包模式 (package)**
- 使用 `mcp-modelservice package` 命令可以将指定文件夹打包在一个名为 project 的文件夹之中，并且提供一个 start.sh 作为启动服务的脚本

```bash
# 启动服务
uvx mcp-modelservice-sdk run --source-path /path/to/your/code --port 8080

# 打包服务（用于生产部署）
uvx mcp-modelservice-sdk package --source-path /path/to/your/code --output my-service.zip

# 查看帮助
uvx mcp-modelservice-sdk --help
```

### 🛠️ 两种架构模式

我们提供两种不同的服务架构模式，您可以根据具体需求选择：

#### 📋 Composed 模式（组合模式）- **推荐**

**工作原理**：
- 创建一个主 FastMCP 实例作为"宿主"
- 每个 Python 文件创建独立的 FastMCP 子实例
- 所有子实例挂载到主实例下，通过分隔符区分不同的工具

**特点**：
- ✅ **统一入口**：所有工具都通过单一端点访问
- ✅ **简化客户端**：客户端只需连接一个地址
- ✅ **资源共享**：更好的资源利用和管理
- ✅ **命名空间**：使用 "+" "_" "." 分隔符自动管理工具命名

**适用场景**：
- 需要统一 API 访问的应用
- 工具之间有协作关系
- 希望简化客户端集成
- 中小型项目或原型开发

**使用示例**：
```bash
# 使用组合模式（默认）
mcp-modelservice run --source-path ./my_tools --mode composed

# 访问地址：http://localhost:8080/mcp-server/mcp
# 工具调用：tool_file1_add, tool_file2_calculate 等
```

#### 🔀 Routed 模式（路由模式）

**工作原理**：
- 每个 Python 文件创建独立的 FastMCP 实例
- 每个实例分配独立的路由路径
- 按照文件目录结构自动生成访问路径

**特点**：
- ✅ **模块隔离**：每个文件模块完全独立
- ✅ **微服务架构**：符合微服务设计原则
- ✅ **独立部署**：可以单独管理和扩展每个模块
- ✅ **清晰分离**：不同功能模块有明确的边界

**适用场景**：
- 大型项目或企业级应用
- 需要模块化部署和管理
- 团队协作开发，不同模块由不同人维护
- 需要独立扩展某些特定功能

**使用示例**：
```bash
# 使用路由模式
mcp-modelservice run --source-path ./my_tools --mode routed

# 访问地址：
# http://localhost:8080/math_tools - 数学工具模块
# http://localhost:8080/text_tools - 文本工具模块
# http://localhost:8080/data_tools - 数据工具模块
```

#### 🆚 模式对比

| 特性 | Composed 模式 | Routed 模式 |
|------|---------------|-------------|
| **访问方式** | 单一端点 | 多个端点 |
| **工具命名** | 自动前缀 | 原始名称 |
| **资源占用** | 较低 | 较高 |
| **部署复杂度** | 简单 | 中等 |
| **扩展性** | 垂直扩展 | 水平扩展 |
| **适用规模** | 中小型 | 大型 |

### 参数说明

| 参数          | 描述                         | 默认值          |
|---------------|------------------------------|-----------------|
| `--source-path` | 包含 Python 代码的文件或目录 | 当前目录        |
| `--port`       | 服务监听端口                 | 8080            |
| `--host`       | 服务监听地址                 | 127.0.0.1       |
| `--mcp-name`   | 服务名称                     | 自动生成        |
| `--mode`       | 架构模式 (composed/routed)    | composed        |


## 🤝 客户端使用

服务启动后，您可以通过以下方式调用：

### 1. 使用浏览器

下载 MCP inspector

访问 `http://localhost:8080/mcp-server/mcp` 查看交互式文档，直接测试您的服务。

### 2. 使用 Python 客户端

```python
import requests
import json

# 调用服务
def call_mcp_tool(tool_name, parameters):
    url = "http://localhost:8080/mcp-server/mcp"
    payload = {
        "jsonrpc": "2.0",
        "method": tool_name,
        "params": parameters,
        "id": 1
    }
    response = requests.post(url, json=payload)
    return response.json()

# 示例调用
result = call_mcp_tool("add", {"a": 5, "b": 3})
print(result)  # 输出: {'jsonrpc': '2.0', 'result': 8, 'id': 1}
```


## 💡 常见问题

### 服务无法启动？

1. 检查端口是否被占用（尝试使用 `--port 9000` 指定其他端口）
2. 确保 Python 代码没有语法错误
3. 查看控制台输出，查找具体错误信息

### 如何选择合适的架构模式？

- **小型项目 < 10个工具**：推荐 `composed` 模式
- **中型项目 10-50个工具**：两种模式都可以，看团队偏好
- **大型项目 > 50个工具**：推荐 `routed` 模式
- **团队协作开发**：推荐 `routed` 模式
- **快速原型开发**：推荐 `composed` 模式

### 如何部署到生产环境？

```bash
# 打包服务
uvx mcp-modelservice-sdk package --source-path /path/to/your/code --output my-service.zip

# 将生成的 zip 文件上传到服务器，然后：
unzip my-service.zip
cd my-service/project
./start.sh  # 启动生产服务
```


## 📚 更多资源

- [完整文档](docs/README.md)
- [架构设计指南](docs/architecture.md)
- [最佳实践](docs/best-practices.md)


## 💖 贡献与反馈

我们欢迎您的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目。如有问题或建议，请提交 [Issues](https://github.com/your-project/issues)。


## Event Store Feature

This package includes support for a SQLite-based event store when using the FastMCP Streamable HTTP transport. This feature enables persistent storage of MCP events and interactions, allowing for:

- History tracking
- Stateful interactions across server restarts
- Analytics and usage statistics

### Enabling the Event Store

To enable the event store, use the `enable_event_store` parameter when creating your MCP application:

```python
from mcp_modelservice_sdk.src.app_builder import create_mcp_application

app = create_mcp_application(
    source_path_str="./my_functions",
    enable_event_store=True,  # Enable the SQLite event store
    event_store_path="./data/mcp_events.db"  # Optional custom path
)
```

By default, the SQLite database will be created in the current working directory as `mcp_events.db`. You can specify a custom path using the `event_store_path` parameter.

### Accessing Event Store Data

The event store tracks:
- Client sessions
- Tool calls with parameters and results
- Resource accesses

The event store instance is available on the application state:

```python
# Access the event store from the app
event_store = app.state.event_store

# Get usage statistics
stats = event_store.get_statistics()

# Get tool call history
tool_calls = event_store.get_tool_call_history(limit=50)
```


---

祝您使用愉快！如有任何疑问，欢迎随时联系我们。