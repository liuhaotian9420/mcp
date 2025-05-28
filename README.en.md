# 🚀 Easy Build & Deploy MCP Services: `mcpy-cli` Guide

*[中文版本](README.md)*

Welcome to the `mcpy-cli`! This guide will help you quickly create, run, convert, and deploy your own MCP (Model Context Protocol) services with minimal effort.

## Overview

This tutorial is divided into several parts:

1. **Easy integration with `fastapi-mcp`**: Learn how to quickly expose an existing FastAPI application as an MCP service.
2. **Building MCP servers natively with `fastmcp`**: Explore how to create MCP servers from scratch using the `fastmcp` library, covering different transport protocols (Stdio, SSE, StreamableHTTP).
3. **Advanced native `fastmcp` usage**: Learn how to integrate `fastmcp` servers into larger ASGI (Starlette) applications and implement streaming tools.
4. **Wrapping external services**: Understand how MCP tools can act as clients to external services.

We'll explore various example files located in the `src/mcp_project/` and `src/mcp_project/examples/` directories.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The workflow runs automatically:

- When pushing to the main branch (runs tests)
- When creating pull requests to the main branch (runs tests)
- When pushing commits with `v*` tags (builds and publishes to PyPI)
- Supports manual triggering from GitHub Actions UI

To release a new version:

1. Update the version in `pyproject.toml`
2. Commit the change: `git commit -am "Bump version to X.Y.Z"`
3. Tag the commit: `git tag vX.Y.Z`
4. Push the changes and tags: `git push && git push --tags`

For more details, see [.github/README.md](.github/README.md).

## Quick Start with UVX

Since this package is available on PyPI, you can quickly use it with `uvx` without installing it permanently:

```bash
# Run the MCP service directly with your own Python tools file
uvx mcpy-cli run --source-path your_tools.py --port 8080

# Or with custom options
uvx mcpy-cli run --source-path your_tools.py --port 9000 --host 0.0.0.0 --mcp-name CustomService
```

This allows you to:
1. Use the MCP SDK without permanently installing it
2. Run the MCP server with your own Python file containing functions
3. Access the MCP tools through the web interface at http://localhost:8080/mcp-server/mcp

## Use Cases

The `mcpy-cli` is particularly well-suited for the following scenarios:

*   **Rapid Prototyping of MCP Services**: Quickly turn a directory of Python scripts or a single utility file into an MCP-accessible service without writing extensive boilerplate for a web framework.
*   **Microservice Architectures**: Structure your project such that each Python file (or subdirectory) becomes a distinct microservice, each with its own set of MCP tools, automatically routed based on the file system structure.
*   **Exposing Python Libraries as Network APIs**: Make existing Python libraries or collections of utility functions available over the network as MCP tools with minimal refactoring.
*   **Internal Tooling and Automation**: Create and deploy internal tools and automation scripts as MCP services for easy access and integration within an organization.
*   **Simplified Deployment of Python Functions**: Package Python functions into runnable services (via the `package` command) that can be deployed in environments supporting Python and the `mcpy-cli`.
*   **Developer-Friendly API Creation**: Enable developers to focus on writing Python functions, with the SDK handling the complexities of exposing them as MCP services and packaging.
*   **Directory-Driven Tool Organization**: Leverage the automatic routing based on filesystem structure to intuitively organize and expose related sets of tools.

## Prerequisites

- Python 3.8+
- `pip` for package installation (or your preferred Python package manager like `uv`)

## Setup

1. **Clone the repository (if not already done):**
   ```bash
   git clone <repository-url>
   cd mcp # or your project root directory
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
   ```

3. **Install core dependencies:**
   This tutorial uses several key libraries. You can install them via pip:
   ```bash
   pip install fastapi uvicorn[standard] pydantic fastapi-mcp fastmcp requests
   ```
   *(Note: `requests` is used by `fastapi_mcp_client_example.py`)*
   Alternatively, if your `pyproject.toml` contains these dependencies, use your project's installation command (e.g., `uv sync` or `pip install -e .`).
   *(Note: Ensure the package names `fastapi-mcp` and `fastmcp` correspond to the libraries you intend to use. `fastmcp` refers to jlowin's library.)*

## Part 1: Easy Integration with `fastapi-mcp`

This approach is ideal if you have an existing FastAPI application and want to expose its endpoints as MCP tools with minimal changes.

**Key Server Example:** `src/mcp_project/fastapi_mcp_example.py`

This file demonstrates:
- A standard FastAPI application with arithmetic operations (`/add`, `/subtract`, etc.).
- Initializing `FastApiMCP` to wrap the FastAPI application.
- Automatic discovery of FastAPI endpoints as MCP tools.
- Custom MCP handlers for listing resources and prompts (`@mcp.server.list_resources()` etc.).
- Mounting the MCP server to the FastAPI application using `mcp.mount()`.

**Running the Server:**
```bash
python src/mcp_project/fastapi_mcp_example.py
```
The service typically runs on `http://localhost:8080`. MCP endpoints are typically available under `/mcp` (e.g., `http://localhost:8080/mcp`).

**Client Example for Part 1:** `src/mcp_project/examples/fastapi_mcp_client_example.py`
This client uses the `requests` library to interact with the `fastapi_mcp_example.py` service. It demonstrates the JSON-RPC communication flow over HTTP/SSE.

**Exploring Part 1:**
1. Run the `fastapi_mcp_example.py` server.
2. In a separate terminal, run `fastapi_mcp_client_example.py`.
3. You can also test the standard FastAPI endpoints directly (e.g., `curl -X POST "http://localhost:8080/add?a=10&b=5"`).

## Part 2: Building MCP Servers Natively with `fastmcp`

The `fastmcp` library (developed by jlowin) allows you to build MCP servers directly, without a pre-existing FastAPI application. This gives you more control and is suitable for creating dedicated MCP services.

Tools are defined by decorating Python functions with `@mcp.tool()`.

**Server Example Files:** `src/mcp_project/examples/`

- **`native_stdio_mcp_example.py` (Stdio Transport)**
  - **Purpose**: For CLI-based tools or subprocess interaction.
  - **Running**: `python src/mcp_project/examples/native_stdio_mcp_example.py`
  - Server communicates via standard input/output.

- **`native_sse_mcp_example.py` (SSE Transport)**
  - **Purpose**: For clients that support Server-Sent Events (SSE).
  - **Running**: `python src/mcp_project/examples/native_sse_mcp_example.py`
  - Serves on `http://127.0.0.1:8001/sse`.

- **`native_streamable_http_mcp_example.py` (StreamableHTTP Transport)**
  - **Purpose**: Recommended for modern web-based MCP services.
  - **Running**: `python src/mcp_project/examples/native_streamable_http_mcp_example.py`
  - Serves on `http://127.0.0.1:8002/mcp`.

**Client Example for Part 2:** `src/mcp_project/examples/native_client_example.py`
This script demonstrates how to connect to each of the above native arithmetic servers using `fastmcp.Client`.

**Exploring Part 2:**
1. For the SSE and StreamableHTTP servers, start the desired server script in one terminal.
2. Run `native_client_example.py` in another terminal. It will guide you through testing each type of native server.

## Part 3: Advanced Native `fastmcp` Usage - ASGI Integration and Streaming

**Key Server Example:** `src/mcp_project/examples/native_advanced_asgi_mcp_example.py`

This example showcases:
- Building a `fastmcp` server (`mcp = FastMCP(...)`).
- Getting an ASGI application from it using `mcp.http_app()`.
- Mounting this MCP ASGI app within a larger Starlette application.
- An asynchronous tool (`a_long_tool_call`) that streams progress updates back to the client (yielding multiple responses).
- Running the combined Starlette application with Uvicorn.

**Running the Server:**
```bash
python src/mcp_project/examples/native_advanced_asgi_mcp_example.py
```
The MCP service will be available under `http://127.0.0.1:8080/mcp-server/mcp`.
This pattern is useful when you need to combine MCP functionality with other HTTP endpoints or ASGI middleware in a single application. You can test its tools (like `a_long_tool_call`) using `fastmcp.Client` as you would in `native_client_example.py`, pointing to the correct URL.

## Part 4: Wrapping External Services

**Key Server Example:** `src/mcp_project/examples/modelservice_mcp_example.py`

This example demonstrates how MCP tools (themselves part of a FastAPI service using `fastapi-mcp`) can call external HTTP services.
- It defines FastAPI endpoints (`/call_workflow`, `/call_agent`).
- The `call_external_service` function within makes `requests.post` calls to external URLs.
- These endpoints are then exposed as MCP tools.

This illustrates that MCP tools are not limited to standalone logic but can orchestrate or interact with other APIs and services.

## General Notes on MCP Client Interaction

- **`fastmcp.Client`**: Used in `native_client_example.py` to interact with `fastmcp`-based servers. It handles different transports (Stdio, SSE, StreamableHTTP) more abstractly.
- **Direct HTTP/JSON-RPC**: Used in `fastapi_mcp_client_example.py` for `fastapi-mcp` services. This shows the underlying JSON-RPC calls typically made over HTTP/SSE.

Key client operations include:
- Initializing a session and capabilities.
- Listing tools.
- Executing tools with parameters.
- Handling single and streaming responses.

## Next Steps

1. **Install dependencies**: Ensure all packages (`fastapi`, `uvicorn`, `pydantic`, `fastapi-mcp`, `fastmcp`, `requests`) are in your environment.
2. **Run the examples**: Go through each part, run the servers, and test with the corresponding client examples.
3. **Experiment**: Modify existing tools or add new ones to different server examples.
4. **Dive deeper**: Explore the `fastapi-mcp` and `fastmcp` documentation for more advanced features like authentication, resource management, and prompt engineering.

This tutorial provides a structured path to understanding and building MCP services. Happy coding! 