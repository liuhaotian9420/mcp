# mcp-modelservice-sdk

🚀 **Easily build and deploy MCP (Model Context Protocol) services from your Python functions**

[![PyPI version](https://badge.fury.io/py/mcp-modelservice-sdk.svg)](https://badge.fury.io/py/mcp-modelservice-sdk)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`mcp-modelservice-sdk` is a powerful toolkit that transforms your Python functions into fully-featured MCP services with minimal configuration. Perfect for developers who want to quickly expose their Python code as MCP tools without the complexity of manual service setup.

## ✨ Key Features

- 📦 **Zero-Config Packaging**: Convert Python functions to MCP services instantly
- 🚀 **One-Command Deployment**: Start services with a single command
- 🔄 **Smart Auto-Routing**: Automatic endpoint generation based on your code structure
- 🌐 **Production Ready**: Built-in support for Docker, cloud platforms, and scaling
- 🛠️ **Developer Friendly**: Interactive testing interface and comprehensive documentation
- 🎯 **Type Safe**: Full support for Python type hints and automatic validation

## 🚀 Quick Start

### Installation

```bash
# Using pip
pip install mcp-modelservice-sdk

# Using uv (recommended)
pip install uv
uv pip install mcp-modelservice-sdk
```

### Basic Usage

1. **Create your Python functions**:
```python
# my_tools.py
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b

def get_weather(city: str) -> str:
    """Get weather information for a city"""
    return f"Weather in {city}: Sunny, 25°C"
```

2. **Run as MCP service**:
```bash
# Start local development server
mcp-modelservice run --source-path my_tools.py --port 8080

# Or with uv
uvx mcp-modelservice-sdk run --source-path my_tools.py --port 8080
```

3. **Test your service**:
   - Visit `http://localhost:8080/mcp` for interactive testing
   - Use any MCP client to connect and call your functions

### Production Packaging

```bash
# Package for deployment
mcp-modelservice package --source-path ./my_code --output my-service.zip

# Extract and deploy
unzip my-service.zip
cd my-service/project
./start.sh
```

## ��️ How It Works

The SDK automatically:
- **Discovers** all functions in your Python files
- **Converts** them to MCP-compatible tools with proper schemas
- **Generates** REST endpoints and documentation
- **Packages** everything into deployable services
- **Provides** interactive testing interfaces
- **Local Development**: Direct execution with `./start.sh`

## 🏛️ Architecture Modes

Choose the architecture that best fits your project needs:

### 📋 Composed Mode (Recommended)

**How it works**:
- Creates one main FastMCP instance as the "host"
- Each Python file gets its own FastMCP sub-instance
- All sub-instances are mounted to the main instance with separators for tool distinction

**Benefits**:
- ✅ **Unified Access**: All tools accessible through a single endpoint
- ✅ **Simplified Client**: Clients only need to connect to one address
- ✅ **Resource Efficiency**: Better resource utilization and management
- ✅ **Namespace Management**: Automatic tool naming with separators ("+", "_", ".")

**Best for**:
- Applications requiring unified API access
- Tools that work together cooperatively
- Simplified client integration
- Small to medium-sized projects or prototypes

**Usage**:
```bash
# Using composed mode (default)
mcp-modelservice run --source-path ./my_tools --mode composed

# Access: http://localhost:8080/mcp-server/mcp
# Tools: tool_file1_add, tool_file2_calculate, etc.
```

### 🔀 Routed Mode

**How it works**:
- Each Python file gets its own independent FastMCP instance
- Each instance gets its own dedicated route path
- Routes are auto-generated based on file directory structure

**Benefits**:
- ✅ **Module Isolation**: Each file module is completely independent
- ✅ **Microservices Architecture**: Follows microservices design principles
- ✅ **Independent Deployment**: Manage and scale each module separately
- ✅ **Clear Separation**: Well-defined boundaries between different functionality

**Best for**:
- Large projects or enterprise applications
- Modular deployment and management needs
- Team collaboration with different people maintaining different modules
- Independent scaling of specific functionalities

**Usage**:
```bash
# Using routed mode
mcp-modelservice run --source-path ./my_tools --mode routed

# Access endpoints:
# http://localhost:8080/math_tools - Math utilities
# http://localhost:8080/text_tools - Text processing
# http://localhost:8080/data_tools - Data manipulation
```

### 🆚 Mode Comparison

| Feature | Composed Mode | Routed Mode |
|---------|---------------|-------------|
| **Access Pattern** | Single endpoint | Multiple endpoints |
| **Tool Naming** | Auto-prefixed | Original names |
| **Resource Usage** | Lower | Higher |
| **Deployment Complexity** | Simple | Medium |
| **Scalability** | Vertical scaling | Horizontal scaling |
| **Best Project Size** | Small-Medium | Large |
| **Team Collaboration** | Simple projects | Complex/distributed teams |

### Architecture Modes

- **Composed Mode**: All tools accessible from a single endpoint
- **Routed Mode**: Directory-based routing with separate endpoints per module

## 🌐 Deployment Options

Deploy anywhere Python runs:
- **Local Development**: Direct execution with `./start.sh`
- **Docker**: Pre-configured Dockerfile included
- **Cloud Platforms**: Compatible with Heroku, AWS Lambda, Google Cloud Run, Azure
- **Traditional Servers**: Standard WSGI/ASGI deployment

## 📚 Client Integration

### Python Client Example
```python
import requests

def call_tool(tool_name, params):
    response = requests.post(
        "http://localhost:8080/mcp",
        json={
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params,
            "id": 1
        }
    )
    return response.json()

# Use your functions
result = call_tool("add_numbers", {"a": 5, "b": 3})
print(result)  # {"jsonrpc": "2.0", "result": 8, "id": 1}
```

### FastMCP Client Example
```python
from fastmcp import FastMCP

client = FastMCP("http://localhost:8080")
result = await client.call_tool("add_numbers", {"a": 5, "b": 3})
```

## ⚙️ Configuration

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source-path` | Path to Python files/directory | Current directory |
| `--port` | Service port | 8080 |
| `--host` | Service host | 127.0.0.1 |
| `--mcp-name` | Service name | Auto-generated |
| `--mode` | Architecture mode (composed/routed) | composed |

### Environment Variables
```bash
# .env file
HOST=0.0.0.0
PORT=8080
MCP_SERVER_NAME=my-service
LOG_LEVEL=INFO
```

## 🤝 Use Cases

Perfect for:
- **Rapid Prototyping**: Quickly expose Python functions as web services
- **Microservices**: Convert existing Python modules to independent services
- **API Generation**: Auto-generate REST APIs from Python functions
- **Tool Integration**: Make Python tools accessible to MCP clients
- **Development Testing**: Interactive testing of Python functions

## 🛠️ Requirements

- **Python**: 3.10 or higher
- **Dependencies**: FastAPI, FastMCP, Pydantic, Uvicorn (auto-installed)

## 📖 Documentation & Support

- **GitHub Repository**: [https://github.com/modelcontextprotocol/mcp-modelservice-sdk](https://github.com/modelcontextprotocol/mcp-modelservice-sdk)
- **Full Documentation**: Available in the GitHub repository
- **Issue Tracking**: Report bugs and request features on GitHub
- **Community**: Join discussions and get help

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/modelcontextprotocol/mcp-modelservice-sdk/blob/main/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/modelcontextprotocol/mcp-modelservice-sdk/blob/main/LICENSE) file for details.

---

**Made with ❤️ for the Python and MCP communities**

Ready to transform your Python functions into powerful MCP services? Install `mcp-modelservice-sdk` today! 