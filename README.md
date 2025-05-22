# 轻松构建与部署 MCP 服务：`mcp-modelservice-sdk` 实战指南

*[English Version](README.en.md)*

欢迎阅读 `mcp-modelservice-sdk` 实战指南！本指南将引导您一步步使用 Python 和 `mcp-modelservice-sdk` 来创建、运行并打包 MCP (模型上下文协议) 服务。通过本 SDK，您可以轻松地将现有的 Python 函数或整个项目转化为结构清晰、易于访问的 MCP 服务。

## `mcp-modelservice-sdk` 概览

`mcp-modelservice-sdk` 是一个 Python 工具包，旨在大幅简化 MCP 服务的开发和部署流程。其核心特性包括：

*   **命令行工具 (CLI)**：提供了 `run` 和 `package` 命令，让您无需编写大量服务器代码即可启动服务或打包应用。
*   **目录驱动的路由**：自动将您 Python 文件（或目录）的结构映射为 MCP 服务的路由，使工具的组织直观易懂。
*   **无缝集成 `fastmcp`**：底层利用 `fastmcp` 的强大功能来创建 MCP 工具和服务器。
*   **快速原型与部署**：无论是快速验证想法，还是将成熟的 Python 工具集部署为服务，SDK 都能提高您的效率。

本指南也会涉及到如何与 `fastapi-mcp` 结合，以及原生使用 `fastmcp` 构建服务的一些模式，这些都是理解 `mcp-modelservice-sdk` 设计理念和实践方式的有益补充。

我们将主要围绕 `mcp-modelservice-sdk` 的使用展开，并穿插 `src/mcp_project/` 和 `src/mcp_project/examples/` 目录下的相关示例进行说明。

## CI/CD (持续集成/持续部署)

本项目已配置 GitHub Actions 实现自动化测试与发布：

*   **自动测试**：每当代码推送至 `main` 分支或创建指向 `main` 分支的拉取请求时，都会自动执行测试。
*   **自动发布**：当推送带有 `v*` (例如 `v0.1.8`) 格式标签的提交时，项目会自动构建并发布到 PyPI。
*   **手动触发**：支持从 GitHub Actions界面手动触发相关工作流程。

**发布新版本流程：**

1.  更新 `pyproject.toml` 文件中的 `version` 字段。
2.  提交版本更新：`git commit -am "Bump version to X.Y.Z"`
3.  为该提交打上版本标签：`git tag vX.Y.Z`
4.  推送提交与标签：`git push && git push --tags`

更多关于 CI/CD 的细节，请参考 [.github/README.md](.github/README.md)。

## 通过 `uvx` 快速体验

`mcp-modelservice-sdk` 已发布到 PyPI。您可以借助 `uvx` (uv 的一个特性，用于执行 PyPI 包的命令) 直接运行 SDK 的 CLI 功能，无需在本地永久安装该包：

```bash
# 使用您自己的 Python 工具文件直接启动 MCP 服务
uvx mcp-modelservice-sdk run --source-path your_tools.py --port 8080

# 或者，指定更多自定义选项
uvx mcp-modelservice-sdk run --source-path your_tools.py --port 9000 --host 0.0.0.0 --mcp-name MyCustomService
```

通过这种方式，您可以：
1.  免安装即时使用 `mcp-modelservice-sdk` 的功能。
2.  指定包含您自定义 Python 函数的文件来运行 MCP 服务。
3.  便捷地通过浏览器（默认地址：`http://localhost:8080/mcp-server/mcp`）访问和测试您的 MCP 工具。

## SDK 核心使用场景

`mcp-modelservice-sdk` 在以下场景中表现尤为出色：

*   **快速原型化 MCP 服务**：无需编写冗余的 Web 框架代码，即可将您的 Python 脚本目录或单个工具文件迅速转化为一个功能完备、可通过 MCP 协议访问的服务。
*   **构建微服务**：您可以依据项目的模块划分，将每个 Python 文件（或子目录）设计成一个独立的微服务。SDK 会根据文件结构自动为其生成独一无二的 MCP 工具集和访问路由。
*   **暴露 Python 库为网络 API**：以极低的学习和重构成本，将您现有的 Python 库或一系列实用函数封装成 MCP 工具，并通过网络提供服务。
*   **开发内部工具与自动化流程**：高效创建并部署内部使用的工具和自动化脚本，将其作为 MCP 服务，便于团队成员的调用和集成。
*   **简化 Python 函数的部署流程**：通过 `package` 命令，将您的 Python 函数及其依赖轻松打包成一个可直接运行的服务，部署到任何支持 Python 和本 SDK 的环境中。
*   **提升 API 开发体验**：让开发者专注于业务逻辑的 Python 函数实现，由 SDK 负责处理服务暴露、请求路由、打包等繁琐工作。
*   **目录驱动的工具组织**：充分利用基于文件系统结构的自动路由特性，实现工具集的直观化组织与管理。

## 环境准备

*   Python 3.8 或更高版本。
*   `pip` (用于安装 Python 包，您也可以使用如 `uv` 等其他您偏好的包管理工具)。

## 安装与设置

1.  **克隆本仓库 (如果尚未操作)：**
    ```bash
    git clone <repository-url> # 请将 <repository-url> 替换为实际的仓库地址
    cd mcp # 或者您项目的根目录
    ```

2.  **创建并激活虚拟环境 (强烈推荐)：**
    ```bash
    python -m venv .venv
    # Windows 系统:
    # .venv\Scripts\activate
    # macOS / Linux 系统:
    source .venv/bin/activate
    ```

3.  **安装核心依赖：**
    本教程及 SDK 的运行依赖一些关键库。您可以通过 `pip` 安装它们：
    ```bash
    pip install fastapi uvicorn[standard] pydantic requests mcp fastmcp # fastapi-mcp 已包含在 mcp 包的 extras 中
    ```
    *（**友情提示**：`requests` 库主要用于示例代码 `fastapi_mcp_client_example.py` 中。`mcp` 包已包含了 `fastapi-mcp` 的功能，安装 `mcp[cli]` 或 `mcp[server]` 会引入它。`fastmcp` 是另一个独立的、由 jlowin 开发的库。）*

    或者，如果您的 `pyproject.toml` 文件已声明了这些依赖，可以直接使用项目配置的安装命令 (例如 `uv pip sync requirements.txt` 或 `pip install -e .`)。

## 第 1 部分：与 `fastapi-mcp` (集成于 `mcp` 包) 轻松集成

如果您已有一个基于 FastAPI 构建的应用，并希望以最小的改动将其API端点暴露为 MCP 工具，这种方式非常适合。

**核心示例：** `src/mcp_project/fastapi_mcp_example.py`

该文件演示了：
- 一个标准的 FastAPI 应用，包含加减乘除等算术运算的 API 端点 (例如 `/add`, `/subtract`)。
- 如何初始化 `FastApiMCP` (通常通过 `mcp.server.configure_server` 或直接实例化) 来包装您的 FastAPI 应用。
- FastAPI 的 API 端点被自动发现并转换为 MCP 工具。
- （可选）为列举资源、提示等 MCP 特定操作定义自定义处理函数 (例如使用 `@mcp.server.list_resources()` 装饰器)。
- 使用 `mcp.mount()` 将 MCP 服务挂载到您的 FastAPI 应用实例上。

**启动服务：**
```bash
python src/mcp_project/fastapi_mcp_example.py
```
服务通常会运行在 `http://localhost:8080`。MCP 相关的端点一般位于 `/mcp` 路径下 (例如 `http://localhost:8080/mcp`)。

**第 1 部分客户端示例：** `src/mcp_project/examples/fastapi_mcp_client_example.py`
这个客户端示例使用 `requests` 库来与 `fastapi_mcp_example.py` 服务进行交互，展示了基于 HTTP/SSE 的 JSON-RPC 通信流程。

**动手实践第 1 部分：**
1.  运行 `fastapi_mcp_example.py` 启动服务端。
2.  在另一个终端窗口中，运行 `fastapi_mcp_client_example.py` 来调用服务。
3.  您也可以直接通过 `curl` 或浏览器插件等工具测试标准的 FastAPI 端点 (例如 `curl -X POST "http://localhost:8080/add?a=10&b=5"`)。

## 第 2 部分：使用 `fastmcp` 原生构建 MCP 服务器

`fastmcp` 库 (由 jlowin 开发) 允许您不依赖预先存在的 FastAPI 应用，从零开始直接构建 MCP 服务器。这种方式赋予您更大的控制力，尤其适合创建专用的 MCP 服务。

在 `fastmcp` 中，您通过 `@mcp.tool()` (通常是 `@your_fastmcp_instance.tool()`) 装饰器来定义 MCP 工具。

**服务端示例文件：** `src/mcp_project/examples/` 目录下

*   **`native_stdio_mcp_example.py` (基于 Stdio 的传输)**
    *   **适用场景**：主要用于命令行工具或需要通过子进程交互的场景。
    *   **运行方式**：`python src/mcp_project/examples/native_stdio_mcp_example.py`
    *   服务通过标准输入/输出 (Stdio) 进行通信。

*   **`native_sse_mcp_example.py` (基于 SSE 的传输)**
    *   **适用场景**：适用于支持服务器发送事件 (SSE) 的客户端。
    *   **运行方式**：`python src/mcp_project/examples/native_sse_mcp_example.py`
    *   服务监听于 `http://127.0.0.1:8001/sse`。

*   **`native_streamable_http_mcp_example.py` (基于可流式 HTTP 的传输)**
    *   **适用场景**：是构建现代化、基于 Web 的 MCP 服务的推荐方式。
    *   **运行方式**：`python src/mcp_project/examples/native_streamable_http_mcp_example.py`
    *   服务监听于 `http://127.0.0.1:8002/mcp`。

**第 2 部分客户端示例：** `src/mcp_project/examples/native_client_example.py`
此脚本演示了如何使用 `fastmcp.Client` 来连接并调用上述几种原生算术运算服务器。

**动手实践第 2 部分：**
1.  对于 SSE 和可流式 HTTP 类型的服务器，请先在独立的终端中启动对应的服务器脚本。
2.  然后在另一个终端中运行 `native_client_example.py`。脚本会引导您逐步测试不同类型的原生服务器。

## 第 3 部分：`fastmcp` 进阶用法 - ASGI 集成与流式工具

**核心示例：** `src/mcp_project/examples/native_advanced_asgi_mcp_example.py`

这个高级示例展示了：
-   如何创建一个 `fastmcp` 服务器实例 (例如 `mcp_instance = FastMCP(...)`)。
-   如何通过 `mcp_instance.http_app()` 从该实例获取一个 ASGI 兼容的应用。
-   如何将这个 MCP ASGI 应用挂载到一个更大型的 Starlette (或其他 ASGI 兼容框架) 应用中。
-   如何定义一个异步工具 (`a_long_tool_call`)，该工具能够将进度更新以流的形式实时推送给客户端 (即一个工具调用可以产生多个响应)。
-   如何使用 Uvicorn 来运行这个组合后的 Starlette 应用。

**启动服务：**
```bash
python src/mcp_project/examples/native_advanced_asgi_mcp_example.py
```
此 MCP 服务将会监听在 `http://127.0.0.1:8080/mcp-server/mcp`。
当您需要在同一个应用中集成 MCP 功能以及其他 HTTP 端点或 ASGI 中间件时，这种模式非常实用。您仍然可以使用 `fastmcp.Client` (如同 `native_client_example.py` 中的做法) 来测试其工具 (例如 `a_long_tool_call`)，只需确保客户端指向正确的服务 URL。

## 第 4 部分：包装外部服务为 MCP 工具

**核心示例：** `src/mcp_project/examples/modelservice_mcp_example.py`

此示例演示了如何让 MCP 工具 (其自身可能是一个 FastAPI 服务的一部分，并使用了 `fastapi-mcp` 或本 SDK) 去调用外部的 HTTP 服务。
-   它定义了若干 FastAPI 端点 (例如 `/call_workflow`, `/call_agent`)。
-   在这些端点对应的处理函数中，`call_external_service` 函数会向一个外部 URL 发起 `requests.post` 请求。
-   这些 FastAPI 端点随后被自动或手动地转换为 MCP 工具。

这清晰地表明，MCP 工具不仅能执行独立的业务逻辑，还可以作为编排层，与其他 API 和服务进行交互。

## 关于 MCP 客户端交互的通用说明

*   **`fastmcp.Client`**：在 `native_client_example.py` 示例中，我们使用它来与基于 `fastmcp` 构建的服务器进行交互。该客户端对不同的传输协议 (Stdio, SSE, StreamableHTTP) 提供了更高级和统一的抽象。
*   **直接 HTTP/JSON-RPC 调用**：在 `fastapi_mcp_client_example.py` 中，主要展示了与 `fastapi-mcp` (或由本 SDK 包装的服务) 进行交互的底层方式。这通常涉及到遵循 JSON-RPC 规范，通过 HTTP/SSE 发送请求和接收响应。

核心的客户端操作一般包括：
-   初始化会话 (Session) 并声明能力 (Capabilities)。
-   列举可用的工具 (Tools)。
-   带参数执行指定的工具。
-   处理单个响应或流式响应。

## 接下来您可以：

1.  **安装依赖**：确保您的开发环境中已安装所有必要的 Python 包 (如 `fastapi`, `uvicorn`, `pydantic`, `mcp`, `fastmcp`, `requests`, 以及本 SDK `mcp-modelservice-sdk`)。
2.  **运行示例代码**：仔细阅读本指南的各个部分，亲手运行示例服务器，并使用对应的客户端脚本进行测试。
3.  **动手实验**：尝试修改现有的 MCP 工具，或者在不同的示例服务器中添加您自己的新工具。
4.  **深入学习**：查阅 `mcp` (包含 `fastapi-mcp`) 和 `fastmcp` 的官方文档，了解更多高级特性，例如身份验证、资源管理、提示工程 (Prompt Engineering) 等。

本指南为您理解和构建 MCP 服务提供了一条清晰的实践路径。祝您编码愉快！
