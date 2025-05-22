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

**1. 本地运行**

- 使用 mcp-modelservice run 命令可以在本地将多个 Python 文件中的函数部署为若干个指定端口的 MCP 服务

**2. 打包文件**
- 使用 mcp-modelservice package 命令可以将指定文件夹打包在一个名为 project 的文件夹之中，并且提供一个 start.sh 作为启动服务的脚本
- 

```bash
# 启动服务
uvx mcp-modelservice-sdk run --source-path /path/to/your/code --port 8080

# 打包服务（用于生产部署）
uvx mcp-modelservice-sdk package --source-path /path/to/your/code --output my-service.zip

# 查看帮助
uvx mcp-modelservice-sdk --help
```

### 🛠️ 两种部署方案

**1. composed 模式**

- 将不同的工具打包在一个固定的路径下，通过工具名称来区分调度

**2. routed 模式**


### 参数说明

| 参数          | 描述                         | 默认值          |
|---------------|------------------------------|-----------------|
| `--source-path` | 包含 Python 代码的文件或目录 | 当前目录        |
| `--port`       | 服务监听端口                 | 8080            |
| `--host`       | 服务监听地址                 | 127.0.0.1       |
| `--mcp-name`   | 服务名称                     | 自动生成        |


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

### 如何部署到生产环境？

```bash
# 打包服务
uvx mcp-modelservice-sdk package --source-path /path/to/your/code --output my-service.zip

# 将生成的 zip 文件上传到服务器，然后：
unzip my-service.zip
cd my-service
python main.py  # 启动生产服务
```


## 📚 更多资源

- [完整文档](docs/README.md)


## 💖 贡献与反馈

我们欢迎您的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目。如有问题或建议，请提交 [Issues](https://github.com/your-project/issues)。


---

祝您使用愉快！如有任何疑问，欢迎随时联系我们。