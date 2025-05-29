# 欢迎使用 123package 服务！

*[English Version](README.md)*

本服务由 `MCPY-CLI`强力驱动，旨在为您提供一套工具，以协助您完成 **执行特定任务**。
<!-- 打包者请注意：请将 '执行特定任务' 替换为对本服务用途的简明用户友好描述。 -->

它使用 `mcpy-cli` 进行打包，以便直接与模型上下文协议 (MCP) 工具进行交互。

## 服务内容

本服务提供：
- 🚀 **即用型工具**：获取强大的功能，用于特定任务。 <!-- 打包者请注意：请替换为非常简短的描述（例如“图像分析”，“文本生成”） -->
- 🐍 **便捷的 Python 集成**：从您的 Python 脚本快速调用工具。
- 🧪 **交互式测试**：直接在浏览器中探索工具。

## 快速上手：使用工具

您可以按照以下步骤开始使用本服务提供的工具：

### 1. 环境要求 (客户端环境)

- **Python 3.7+**：确保您已安装兼容的 Python 版本。
- **`requests` 库**：您需要此库向服务发出 HTTP 请求。如果尚未安装，请运行：
  ```bash
  pip install requests
  ```

### 2. 服务接入点

服务地址：
- **基础 URL**：`http://0.0.0.0:8080`
- **交互式测试页面**：在浏览器中访问 `http://0.0.0.0:8080/mcp` 查看可用工具并进行交互式测试。

### 3. 调用工具 (Python 示例)

您可以使用简单的 Python 脚本调用任何工具。示例如下：

```python
import requests
import json

# --- 配置信息 ---
SERVICE_BASE_URL = "http://0.0.0.0:8080"  # 如果服务托管在其他地方，请替换此URL
TOOL_NAME = "your_tool_name_here"  # 请替换为实际的工具名称 (参见“可用工具”部分)
PARAMETERS = {
    "param1": "value1",  # 请替换为工具所需的实际参数
    "param2": 123
}

# --- 辅助函数 ---
def call_mcp_tool(base_url, tool_name, params):
    """调用 MCP 工具并返回 JSON 响应"""
    endpoint = f"{base_url}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "method": tool_name,
        "params": params,
        "id": 1  # 可以是任何唯一ID
    }
    headers = {'Content-Type': 'application/json'}

    print(f"尝试在 '{endpoint}' 调用工具 '{tool_name}'，参数为: {params}")

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30) # 30秒超时
        response.raise_for_status()  # 针对错误的响应 (4XX 或 5XX) 抛出 HTTPError
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"发生 HTTP 错误: {http_err}")
        print(f"响应内容: {response.content}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"发生连接错误: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"发生超时错误: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求过程中发生意外错误: {req_err}")
    except json.JSONDecodeError:
        print(f"解析 JSON 响应失败。原始响应: {response.text}")
    return None

# --- 主执行逻辑 ---
if __name__ == "__main__":
    print(f"正在调用 MCP 服务 '{TOOL_NAME}'...")
    result = call_mcp_tool(SERVICE_BASE_URL, TOOL_NAME, PARAMETERS)

    if result:
        print("\n--- 服务响应 ---")
        if 'result' in result:
            print("调用成功!")
            print(json.dumps(result['result'], indent=2, ensure_ascii=False))
        elif 'error' in result:
            print("服务返回错误:")
            print(json.dumps(result['error'], indent=2, ensure_ascii=False))
        else:
            print("意外的响应格式:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n未收到响应或调用过程中发生错误。")

```

**请记得：**
- 将 `your_tool_name_here` 替换为您想使用的工具的实际名称。
- 使用该工具所需的正确输入更新 `PARAMETERS` 字典。

### (可选) 使用 FastMCP 客户端

如果您更喜欢并且已安装 `fastmcp` 库 (`pip install fastmcp`)，您也可以使用其客户端：

```python
# import asyncio
# from fastmcp import FastMCP
#
# async def main():
#     client = FastMCP("http://0.0.0.0:8080")
#     try:
#         # 列出可用工具
#         # tools = await client.list_tools()
#         # print("可用工具:", tools)
#
#         # 调用特定工具
#         # result = await client.call_tool("your_tool_name_here", {"param1": "value1"})
#         # print("工具结果:", result)
#     except Exception as e:
#         print(f"发生错误: {e}")
#     finally:
#         await client.close()
#
# if __name__ == "__main__":
#     asyncio.run(main())
```

## 可用工具

以下是本服务中可用的工具列表。此部分是根据打包的 Python 函数自动生成的。

### `add_two_numbers`

**函数签名:** `add_two_numbers(a: int, b: int) -> int`

**描述:**
```
_summary_

Args:
    a (int): _description_
    b (int): _description_

Returns:
    int: _description_

Additional comments:
# The function only adds integers.

```

**源文件:** `simple_tool.py`

---


## 基本故障排除 (客户端)

如果您在尝试调用工具时遇到问题：

1.  **检查服务 URL**：确保您脚本中的 `SERVICE_BASE_URL` 与提供的一致 (`http://0.0.0.0:8080`)。
2.  **验证工具名称**：对照“可用工具”列表仔细检查工具名称。名称区分大小写。
3.  **检查参数**：确保您发送的参数与工具期望的签名（名称、类型和参数数量）匹配。
4.  **网络连接**：确认您可以从客户端计算机访问服务接入点。
5.  **检查服务器日志 (如果可访问)**：如果您可以访问运行此服务的服务器日志，它们可能会提供有关错误的更多详细信息。
6.  **交互式测试页面**：使用 `http://0.0.0.0:8080/mcp` 页面直接测试工具。这有助于判断问题是出在您的客户端代码还是工具本身。

## 支持

-   有关此 `123package` 服务中**工具功能**的问题或疑问，请联系向您提供此服务的人员或团队。
-   如果您怀疑 `mcpy-cli` **打包工具本身**存在问题，您可以在 [mcpy-cli GitHub 仓库](https://github.com/liuhaotian9420/mcp) 找到更多信息或报告问题。

---

🎉 祝您使用愉快！