# 🚀 MCPY-CLI: 快速从 Python 文件构建 MCP 服务

*[English Version](README.en.md)*

欢迎使用 `mcpy-cli`！本指南将帮助您快速上手，通过简单的步骤创建、运行、转换和部署自己的 MCP (模型上下文协议) 服务。


## 什么是 `mcpy-cli`？

这是一个专为简化 MCP 服务开发而设计的工具包。它能帮助您：
- 📦 **快速打包**：将一个或是多个 Python 函数或脚本转换为标准 MCP 服务
- 🚀 **一键部署**：通过命令行快速启动或发布服务
- 🔄 **自动路由**：根据文件结构自动生成服务接口
- 🌐 **灵活配置**：支持多种传输协议，持久化和缓存


## 🔥 快速开始

### 1. 环境要求：

Python >= 3.10, 且安装了 FastMCP, 推荐安装 uv

```bash
# 使用 pip 下载
pip install mcpy-cli

# 使用 uv (如已安装)
uv pip install mcpy-cli

# 使用 uv (未安装)
pip install uv
uv pip install mcpy-cli

```


### 2. MCP 服务示例

```bash
mcpy-cli example
```

### 3. 搭建 MCP 服务

```bash
# 假设在根目录下有一个 sample_tools.py 的文件
mcpy-cli run --source-path sample_tools.py
```

或者如果你安装了 uv

```bash
uvx --from mcpy-cli mcpy-cli --source-path sample_tools.py run
```

服务启动后，访问测试页面： http://localhost:8080/mcp-server/mcp

**推荐使用 MCP inspector 打开该页面**

## 📖 使用指南

### 🔬 核心工具：run & package

本项目提供两种将 .py 脚本转换为 MCP 服务的工具，本地运行工具（run）和打包（package)

**1. 本地运行**

- 使用 `mcpy-cli run` 命令可以在本地将多个 Python 文件中的函数部署为指定端口的 MCP 服务
- 支持自动重载，适合开发调试

**2. 打包**
- 使用 `mcpy-cli package` 命令可以将指定文件夹打包在一个名为 project 的文件夹之中
- 提供一个 start.sh 作为启动服务的脚本，方便部署和修改

```bash
# 启动服务
mcpy-cli run --source-path /path/to/your/code --port 8080
# 或者使用 uvx
uvx mcpy-cli run --source-path /path/to/your/code --port 8080

# 打包服务（用于生产部署）
mcpy-cli package --source-path /path/to/your/code --package-name my-service
# 或者使用 uvx
uvx mcpy-cli package --source-path /path/to/your/code --package-name my-service

# 查看帮助
mcpy-cli --help
# 或者使用 uvx
uvx mcpy-cli --help
```

### 🛠️ 两种架构模式

本项目提供两种不同的 MCP 服务架构，您可以根据具体需求选择：

#### 📋 Composed 模式（组合模式）- **默认**

**工作原理**：
- 创建一个主 FastMCP 实例作为"宿主"
- 每个 Python 文件创建独立的 FastMCP 子实例
- 所有子实例挂载到主实例下，通过前缀+分隔符的方式区分不同的工具

**使用示例**：
```bash
# 使用组合模式（默认）
mcpy-cli run --source-path ./my_tools --mode composed

# 访问地址：http://localhost:8080/mcp-server/mcp
# 工具调用：tool_file1_add, tool_file2_calculate 等
```

#### 🔀 Routed 模式（路由模式）

**工作原理**：
- 每个 Python 文件创建独立的 FastMCP 实例
- 每个实例分配独立的路由路径
- 按照文件目录结构自动生成访问路径


**使用示例**：
```bash
# 使用路由模式
mcpy-cli run --source-path ./my_tools --mode routed

# 访问地址：
# http://localhost:8080/math_tools - 数学工具模块
# http://localhost:8080/text_tools - 文本工具模块
# http://localhost:8080/data_tools - 数据工具模块
```

### 基础参数说明

| 参数          | 描述                         | 默认值          |
|---------------|------------------------------|-----------------|
| `--source-path` | 包含 Python 代码的文件或目录 | 当前目录        |
| `--port`       | 服务监听端口                 | 8080            |
| `--host`       | 服务监听地址                 | 127.0.0.1       |
| `--mcp-name`   | 服务名称                     | 自动生成        |
| `--mode`       | 架构模式 (composed/routed)    | composed        |


## 🤝 客户端使用

使用本地运行工具启动服务后，您可以通过以下方式调用：

### 1. MCP Inspector

使用 [MCP Inspector](https://github.com/modelcontextprotocol/inspector)，在左上角选择【streamable-http】，输入生成的服务 url （默认地址为 http://localhost:8080/mcp-server/mcp)

### 2. 使用支持 MCP 的客户端

以 CherryStudio 为例

## 🧀 进阶配置

### 1. 服务持久化

`mcpy-cli` 支持通过事件存储（EventStore）实现服务持久化和状态恢复功能。当启用此特性时，服务会将 JSON-RPC 消息存储起来，允许在服务中断或重启后从特定事件点恢复执行。

- **实现方式**：默认使用 `SQLiteEventStore`，将事件数据保存在本地 SQLite 数据库文件中。
- **启用方法**：在启动服务时，使用 `--enable-event-store` 标志。
- **数据库路径**：可以通过 `--event-store-path` 参数指定事件存储数据库文件的路径。如果未指定，默认为 `./mcp_event_store.db`。

```bash
# 启用事件存储并指定数据库路径
mcpy-cli run --source-path ./my_tools --enable-event-store --event-store-path ./my_service_events.db
```

此功能对于需要长时间运行或维护会话状态的 MCP 服务特别有用。

### 2. 缓存

为了提高性能并减少重复计算，工具提供了会话级别的工具调用缓存（`SessionToolCallCache`）。

- **工作机制**：此缓存是内存中的，它会存储在特定用户会话中工具调用的结果。当在同一会话中以相同的参数再次调用同一工具时，可以直接从缓存中返回结果，而无需重新执行工具函数。
- **适用场景**：此缓存主要在“有状态 JSON 响应模式”（stateful JSON response mode）下激活并发挥作用。
- **生命周期**：缓存内容与用户会话绑定，会话结束或清除时，相关缓存也会被清除。

此机制有助于优化那些在会话中可能被频繁调用的工具的响应速度。

## 📚 更多资源

- [完整文档](docs/README.md)
- [架构设计指南](docs/architecture.md)
- [最佳实践](docs/best-practices.md)
