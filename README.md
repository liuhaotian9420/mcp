# MCP 项目教程

*[English Version](README.en.md)*

欢迎来到 MCP (模型上下文协议) 项目教程！本指南将引导您使用 Python 创建启用 MCP 的服务，主要使用 `fastapi-mcp` 和 `fastmcp` 库。

## 概述

本教程分为几个部分：

1.  **与 `fastapi-mcp` 轻松集成**：了解如何快速将现有的 FastAPI 应用程序公开为 MCP 服务。
2.  **使用 `fastmcp` 原生构建 MCP 服务器**：探索如何使用 `fastmcp` 库从头开始创建 MCP 服务器，涵盖不同的传输协议（Stdio、SSE、可流式 HTTP）。
3.  **高级原生 `fastmcp` 用法**：了解如何将 `fastmcp` 服务器集成到更大的 ASGI (Starlette) 应用程序中并实现流式工具。
4.  **包装外部服务**：理解 MCP 工具如何充当外部服务的客户端。

我们将探讨位于 `src/mcp_project/` 和 `src/mcp_project/examples/` 目录中的各种示例文件。

## CI/CD

本项目使用 GitHub Actions 进行持续集成和部署。工作流程在以下情况下自动运行：

- 推送到主分支时运行测试
- 拉取请求到主分支时运行测试
- 推送带 `v*` 标签的提交时构建并发布到 PyPI
- 支持从 GitHub Actions UI 手动触发

要发布新版本：

1. 更新 `pyproject.toml` 中的版本号
2. 提交更改：`git commit -am "Bump version to X.Y.Z"`
3. 添加标签：`git tag vX.Y.Z`
4. 推送更改和标签：`git push && git push --tags`

更多详情请参阅 [.github/README.md](.github/README.md)。

## 使用 UVX 快速开始

由于本包已发布在 PyPI 上，您可以使用 `uvx` 快速使用它，无需永久安装：

```bash
# 直接使用您自己的 Python 工具文件运行 MCP 服务
uvx mcp-modelservice-sdk run --source-path your_tools.py --port 8080

# 或使用自定义选项
uvx mcp-modelservice-sdk run --source-path your_tools.py --port 9000 --host 0.0.0.0 --mcp-name CustomService
```

这使您能够：
1. 无需永久安装即可使用 MCP SDK
2. 使用包含函数的自己的 Python 文件运行 MCP 服务器
3. 通过网页界面访问 MCP 工具：http://localhost:8080/mcp-server/mcp

## 使用场景

`mcp-modelservice-sdk` 特别适用于以下场景：

*   **快速原型化 MCP 服务**：无需为Web框架编写大量样板代码，即可快速将 Python 脚本目录或单个实用工具文件转换为可通过 MCP 访问的服务。
*   **微服务架构**：您可以将项目结构化，使每个 Python 文件（或子目录）成为一个独特的微服务，每个微服务都拥有一套自己的 MCP 工具，并根据文件系统结构自动路由。
*   **将 Python 库暴露为网络 API**：以最少的重构工作，将现有的 Python 库或实用函数集合作为 MCP 工具通过网络提供。
*   **内部工具和自动化**：创建和部署内部工具及自动化脚本作为 MCP 服务，以便在组织内部轻松访问和集成。
*   **简化 Python 函数的部署**：将 Python 函数打包成可运行的服务（通过 `package` 命令），这些服务可以部署在支持 Python 和 `mcp-modelservice-sdk` 的环境中。
*   **开发者友好的 API 创建**：使开发人员能够专注于编写 Python 函数，由 SDK 处理将其公开为 MCP 服务和打包的复杂性。
*   **目录驱动的工具组织**：利用基于文件系统结构的自动路由功能，直观地组织和暴露相关工具集。

## 先决条件

- Python 3.8+
- 用于包安装的 `pip`（或您首选的 Python 包管理器，如 `uv`）

## 设置

1.  **克隆存储库（如果尚未克隆）：**
    ```bash
    git clone <repository-url>
    cd mcp # 或您的项目根目录
    ```

2.  **创建虚拟环境（推荐）：**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # 在 Windows 上使用 .venv\\Scripts\\activate
    ```

3.  **安装核心依赖项：**
    本教程使用几个关键库。您可以通过 pip 安装它们：
    ```bash
    pip install fastapi uvicorn[standard] pydantic fastapi-mcp fastmcp requests
    ```
    *（注意：`requests` 被 `fastapi_mcp_client_example.py` 使用）*
    或者，如果您的 `pyproject.toml` 包含这些依赖项，请使用您项目的安装命令（例如 `uv sync` 或 `pip install -e .`）。
    *（注意：确保包名称 `fastapi-mcp` 和 `fastmcp` 与您打算使用的库相对应。`fastmcp` 指的是 jlowin 的库。）*

## 第 1 部分：与 `fastapi-mcp` 轻松集成

如果您有一个现有的 FastAPI 应用程序并希望以最少的更改将其端点公开为 MCP 工具，则此方法非常理想。

**关键服务器示例：** `src/mcp_project/fastapi_mcp_example.py`

此文件演示了：
- 具有算术运算（`/add`、`/subtract` 等）的标准 FastAPI 应用程序。
- 初始化 `FastApiMCP` 以包装 FastAPI 应用程序。
- 自动发现 FastAPI 端点作为 MCP 工具。
- 用于列出资源和提示的自定义 MCP 处理程序（`@mcp.server.list_resources()` 等）。
- 使用 `mcp.mount()` 将 MCP 服务器挂载到 FastAPI 应用程序。

**运行服务器：**
```bash
python src/mcp_project/fastapi_mcp_example.py
```
该服务通常在 `http://localhost:8080` 上运行。MCP 端点通常在 `/mcp` 下可用（例如 `http://localhost:8080/mcp`）。

**第 1 部分的客户端示例：** `src/mcp_project/examples/fastapi_mcp_client_example.py`
此客户端使用 `requests` 库与 `fastapi_mcp_example.py` 服务进行交互。它演示了通过 HTTP/SSE 的 JSON-RPC 通信流程。

**探索第 1 部分：**
1. 运行 `fastapi_mcp_example.py` 服务器。
2. 在单独的终端中，运行 `fastapi_mcp_client_example.py`。
3. 您也可以直接测试标准的 FastAPI 端点（例如 `curl -X POST "http://localhost:8080/add?a=10&b=5"`）。

## 第 2 部分：使用 `fastmcp` 原生构建 MCP 服务器

`fastmcp` 库（由 jlowin 开发）允许您直接构建 MCP 服务器，而无需预先存在的 FastAPI 应用程序。这为您提供了更多控制权，并且适用于创建专用的 MCP 服务。

通过使用 `@mcp.tool()` 装饰 Python 函数来定义工具。

**服务器示例文件：** `src/mcp_project/examples/`

-   **`native_stdio_mcp_example.py` (Stdio 传输)**
    -   **目的**：用于基于 CLI 的工具或子进程交互。
    -   **运行**：`python src/mcp_project/examples/native_stdio_mcp_example.py`
    -   服务器通过标准输入/输出进行通信。

-   **`native_sse_mcp_example.py` (SSE 传输)**
    -   **目的**：用于支持服务器发送事件 (SSE) 的客户端。
    -   **运行**：`python src/mcp_project/examples/native_sse_mcp_example.py`
    -   在 `http://127.0.0.1:8001/sse` 上提供服务。

-   **`native_streamable_http_mcp_example.py` (可流式 HTTP 传输)**
    -   **目的**：推荐用于现代基于 Web 的 MCP 服务。
    -   **运行**：`python src/mcp_project/examples/native_streamable_http_mcp_example.py`
    -   在 `http://127.0.0.1:8002/mcp` 上提供服务。

**第 2 部分的客户端示例：** `src/mcp_project/examples/native_client_example.py`
此脚本演示了如何使用 `fastmcp.Client` 连接到上述每个原生算术服务器。

**探索第 2 部分：**
1. 对于 SSE 和可流式 HTTP 服务器，在一个终端中启动所需的服务器脚本。
2. 在另一个终端中运行 `native_client_example.py`。它将引导您测试每种类型的原生服务器。

## 第 3 部分：高级原生 `fastmcp` 用法 - ASGI 集成和流式处理

**关键服务器示例：** `src/mcp_project/examples/native_advanced_asgi_mcp_example.py`

此示例展示了：
-   构建一个 `fastmcp` 服务器 (`mcp = FastMCP(...)`)。
-   使用 `mcp.http_app()` 从中获取 ASGI 应用程序。
-   在更大的 Starlette 应用程序中挂载此 MCP ASGI 应用程序。
-   一个异步工具 (`a_long_tool_call`)，可将进度更新流式传输回客户端（产生多个响应）。
-   使用 Uvicorn 运行组合的 Starlette 应用程序。

**运行服务器：**
```bash
python src/mcp_project/examples/native_advanced_asgi_mcp_example.py
```
MCP 服务将在 `http://127.0.0.1:8080/mcp-server/mcp` 下可用。
当您需要在单个应用程序中将 MCP 功能与其他 HTTP 端点或 ASGI 中间件结合使用时，此模式非常有用。您可以像 `native_client_example.py` 操作一样，使用 `fastmcp.Client` 测试其工具（如 `a_long_tool_call`），指向正确的 URL。

## 第 4 部分：包装外部服务

**关键服务器示例：** `src/mcp_project/examples/modelservice_mcp_example.py`

此示例演示了 MCP 工具（本身是 FastAPI 服务的一部分，使用 `fastapi-mcp`）如何调用外部 HTTP 服务。
-   它定义了 FastAPI 端点 (`/call_workflow`, `/call_agent`)。
-   其中的 `call_external_service` 函数向外部 URL 发出 `requests.post` 请求。
-   然后将这些端点公开为 MCP 工具。

这说明 MCP 工具不仅限于独立逻辑，还可以编排或与其他 API 和服务进行交互。

## 关于 MCP 客户端交互的一般说明

- **`fastmcp.Client`**：在 `native_client_example.py` 中用于与基于 `fastmcp` 的服务器进行交互。它更抽象地处理不同的传输（Stdio、SSE、StreamableHTTP）。
- **直接 HTTP/JSON-RPC**：在 `fastapi_mcp_client_example.py` 中用于 `fastapi-mcp` 服务。这显示了通常通过 HTTP/SSE 进行的底层 JSON-RPC 调用。

关键客户端操作包括：
- 初始化会话和功能。
- 列出工具。
- 使用参数执行工具。
- 处理单个和流式响应。

## 后续步骤

1.  **安装依赖项**：确保所有包（`fastapi`、`uvicorn`、`pydantic`、`fastapi-mcp`、`fastmcp`、`requests`）都在您的环境中。
2.  **运行示例**：通读每个部分，运行服务器，并使用相应的客户端示例进行测试。
3.  **进行实验**：修改现有工具或向不同的服务器示例添加新工具。
4.  **深入研究**：探索 `fastapi-mcp` 和 `fastmcp` 文档，以了解更高级的功能，如身份验证、资源管理和提示工程。

本教程为理解和构建 MCP 服务提供了一条结构化的路径。祝您编码愉快！
