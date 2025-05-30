# Welcome to the 123package Service!

*[中文版本](README_zh.md)*

This service, powered by `MCPY-CLI`, provides a set of tools to help you with **performing specific tasks**. <!-- Note to packager: Please replace 'performing specific tasks' with a brief, user-friendly description of what this service does. -->

It was packaged using `mcpy-cli` to make interacting with its Model Context Protocol (MCP) tools straightforward.

## What's Inside?

This service offers:
- 🚀 **Ready-to-use Tools**: Access powerful functionalities for specific tasks. <!-- Note to packager: Replace with a very short (2-3 words) description, e.g., 'image analysis', 'text generation' -->
- 🐍 **Easy Python Integration**: Quickly call tools from your Python scripts.
- 🧪 **Interactive Testing**: Explore tools directly in your browser.

## Getting Started: Using the Tools

Here's how you can start using the tools provided by this service:

### 1. Prerequisites (for your client environment)

- **Python 3.7+**: Ensure you have a compatible Python version installed.
- **`requests` library**: You'll need this library to make HTTP calls to the service. Install it if you haven't already:
  ```bash
  pip install requests
  ```

### 2. Service Endpoint

The service is available at:
- **Base URL**: `http://0.0.0.0:8080`
- **Interactive Test Page**: Visit `http://0.0.0.0:8080/mcp` in your browser to see available tools and test them interactively.

### 3. Calling a Tool (Python Example)

You can call any tool using a simple Python script. Here's an example:

```python
import requests
import json

# --- Configuration ---
SERVICE_BASE_URL = "http://0.0.0.0:8080"  # Replace if the service is hosted elsewhere
TOOL_NAME = "your_tool_name_here"  # Replace with the actual tool name (see 'Available Tools' section)
PARAMETERS = {
    "param1": "value1",  # Replace with actual parameters for the tool
    "param2": 123
}

# --- Helper Function ---
def call_mcp_tool(base_url, tool_name, params):
    """Calls an MCP tool and returns the JSON response."""
    endpoint = f"{base_url}/mcp"
    payload = {
        "jsonrpc": "2.0",
        "method": tool_name,
        "params": params,
        "id": 1  # Can be any unique ID
    }
    headers = {'Content-Type': 'application/json'}

    print(f"Attempting to call tool '{tool_name}' at '{endpoint}' with parameters: {params}")

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30) # 30-second timeout
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred with the request: {req_err}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response. Raw response: {response.text}")
    return None

# --- Main Execution ---
if __name__ == "__main__":
    print(f"Calling MCP service '{TOOL_NAME}'...")
    result = call_mcp_tool(SERVICE_BASE_URL, TOOL_NAME, PARAMETERS)

    if result:
        print("\n--- Service Response ---")
        if 'result' in result:
            print("Success!")
            print(json.dumps(result['result'], indent=2))
        elif 'error' in result:
            print("Error from service:")
            print(json.dumps(result['error'], indent=2))
        else:
            print("Unexpected response format:")
            print(json.dumps(result, indent=2))
    else:
        print("\nNo response received or an error occurred during the call.")

```

**Remember to:**
- Replace `your_tool_name_here` with the actual name of the tool you want to use.
- Update the `PARAMETERS` dictionary with the correct inputs for that tool.

### (Optional) Using the FastMCP Client

If you prefer, and have the `fastmcp` library installed (`pip install fastmcp`), you can also use its client:

```python
# import asyncio
# from fastmcp import FastMCP
#
# async def main():
#     client = FastMCP("http://0.0.0.0:8080")
#     try:
#         # List available tools
#         # tools = await client.list_tools()
#         # print("Available tools:", tools)
#
#         # Call a specific tool
#         # result = await client.call_tool("your_tool_name_here", {"param1": "value1"})
#         # print("Tool result:", result)
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         await client.close()
#
# if __name__ == "__main__":
#     asyncio.run(main())
```

## Available Tools

Below is a list of tools available in this service. This section is automatically generated based on the packaged Python functions.

### `add_two_numbers`

**Signature:** `add_two_numbers(a: int, b: int) -> int`

**Description:**
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

**Source File:** `simple_tool.py`

---


## Basic Troubleshooting (Client-Side)

If you encounter issues when trying to call a tool:

1.  **Check Service URL**: Ensure the `SERVICE_BASE_URL` in your script matches the one provided (`http://0.0.0.0:8080`).
2.  **Verify Tool Name**: Double-check the tool name against the "Available Tools" list. Names are case-sensitive.
3.  **Inspect Parameters**: Make sure the parameters you're sending match the tool's expected signature (name, type, and number of parameters).
4.  **Network Connectivity**: Confirm you have network access to the service endpoint from your client machine.
5.  **Check Server Logs (if accessible)**: If you have access to the server logs where this service is running, they might provide more details on errors.
6.  **Interactive Test Page**: Use the `http://0.0.0.0:8080/mcp` page to test the tool directly. This can help isolate if the issue is with your client code or the tool itself.

## Support

-   For questions or issues related to the **functionality of the tools** within this `123package` service, please contact the person or team who provided you with this service.
-   If you suspect an issue with the `mcpy-cli` **packaging tool itself**, you can find more information or report issues at the [mcpy-cli GitHub repository](https://github.com/liuhaotian9420/mcp).

---

🎉 Happy Hacking!