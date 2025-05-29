# 📝 MCP-CLI 实战教程：从零开发到服务上线

本教程将带你从零开始，基于 mcpy-cli 快速开发、运行、打包并调用一个自定义 MCP 服务。所有步骤均结合实际代码与命令行操作，适合新手和进阶用户。

---

## 1. 编写你的工具函数

以最简单的加法工具为例，新建 `my_tools.py`：

```python
from typing import Dict

def add(a: float, b: float) -> Dict[str, float]:
    """加法工具：返回 a + b 的结果"""
    return {"result": a + b}
```

你可以在一个文件中定义多个函数，每个函数都可以被暴露为 MCP 工具。

---

## 2. 用 mcpy-cli 启动本地服务

在命令行中运行（假设你已安装 mcpy-cli）：

```powershell
mcpy-cli run --source-path my_tools.py --host 127.0.0.1 --port 8080
```

- 默认会自动发现所有带类型注解的函数并暴露为工具。
- 访问 http://127.0.0.1:8080/mcp/docs 可查看自动生成的 OpenAPI 文档。

---

## 3. 打包你的服务

将工具打包为可分发的 MCP 服务包：

```powershell
mcpy-cli package --source-path my_tools.py --package-name my_mcp_service
```

- 会生成包含 `start.sh`、README、依赖等的完整包，可直接部署。

---

## 4. 客户端调用示例

你可以用 Python 客户端调用服务（参考 `src/mcp-tutorial/examples/client.py`）：

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://127.0.0.1:8080/mcp") as client:
        result = await client.call_tool("add", {"a": 1, "b": 2})
        print(result)

asyncio.run(main())
```

---

## 5. 进阶用法

### 多文件/多模块组合
- 支持传入目录，自动发现所有 Python 文件并挂载为多路由服务。
- 支持 Composed（单入口）与 Routed（多入口）两种模式，详见 `docs/architecture-modes.md`。

### 缓存与会话
- MCP-CLI 内置会话级缓存（`SessionToolCallCache`），提升重复调用效率。

### 常见问题
- 工具未被发现？请确保函数有类型注解和 docstring。
- 端口冲突？更换 `--port` 参数。
- 详细日志：加 `--log-level DEBUG`。

---

## 6. 参考与更多
- 进阶示例见 `src/mcp-tutorial/examples/servers/` 目录。
- 详细参数与高级配置见 `docs/README.md`。
- 遇到问题可查阅 `docs/qa.md`。

---
