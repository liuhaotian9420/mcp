# mcpy-cli

🚀 **Effortlessly transform Python functions into production-ready MCP services**

[![PyPI version](https://badge.fury.io/py/mcpy-cli.svg)](https://badge.fury.io/py/mcpy-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`mcpy-cli` is a powerful toolkit designed to simplify creating, running, and deploying Model Context Protocol (MCP) services. It transforms ordinary Python functions into fully-featured MCP tools with automatic schema generation, endpoint creation, and interactive documentation.

## ✨ Key Features

- 📦 **Automatic Function Discovery**: Scans Python files and detects functions without additional markup required
- 🔄 **Dual Architecture Modes**:
  - **Composed Mode**: All tools under a single endpoint with automatic namespacing
  - **Routed Mode**: Microservice-style with directory-based routing
- 🚀 **Flexible Deployment Options**:
  - `run` command for local development with hot reloading
  - `package` command for production deployment with start scripts
- 🌐 **Complete JSON-RPC Implementation**: Full compliance with MCP protocol specification
- 🔧 **Interactive Web Interface**: Built-in testing page at `/mcp-server/mcp`
- 🎨 **Type-Safe by Design**: Automatic validation using Python type hints and docstrings

## 🚀 Quick Start

### Installation

```bash
# Using pip
pip install mcpy-cli

# Using uv (recommended for faster dependency resolution)
pip install uv
uv pip install mcpy-cli
```

### Building Your First MCP Service

1. **Create a Python file with functions**:
```python
# math_tools.py
def add(a: float, b: float) -> float:
    """Add two numbers and return the result"""
    return a + b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the result"""
    return a * b
```

2. **Create another file for different functionality**:
```python
# text_tools.py
def concatenate(text1: str, text2: str) -> str:
    """Join two text strings together"""
    return text1 + text2
    
def word_count(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())
```

3. **Run in development mode**:
```bash
# Start development server with auto-reload
mcp-modelservice run --source-path ./ --port 8080 --reload True

# Or using uvx without installation
uvx mcpy-cli run --source-path ./ --port 8080 --reload True
```

4. **Test your service**:
   - Open `http://localhost:8080/mcp-server/mcp` in your browser
   - Try calling functions with the interactive interface:
     - In Composed mode (default): `tool_math_tools_add`, `tool_text_tools_word_count`
     - In Routed mode: Navigate to each module's endpoint

### Production Packaging

1. **Package your service for deployment**:
```bash
# Create a deployable package with all dependencies
mcp-modelservice package --source-path ./my_project --package-name math-text-tools

# A zip file will be created: math-text-tools.zip
```

2. **Deploy on your server**:
```bash
# Extract the package
unzip math-text-tools.zip

# Navigate to the project directory
cd math-text-tools/project

# Run the start script (works on Linux/macOS)
chmod +x start.sh  # Make executable if needed
./start.sh

# On Windows, you can use:
# start.bat  # Will be included in the package
```

3. **Deployment Structure**:
The package contains:
- Your source code in its original structure
- A generated `start.sh` script with all necessary parameters
- A `requirements.txt` file with all dependencies
- README files with usage instructions

## 🔧 How It Works: Technical Details

The SDK implements a sophisticated pipeline to convert Python functions to MCP services:

1. **Function Discovery & Analysis**
   - Recursively scans source directories for Python files
   - Imports each file and extracts function objects with introspection
   - Analyzes signatures, type annotations, and docstrings
   - Groups functions by file for organizational structure

2. **FastMCP Instance Creation**
   - Creates FastMCP instances for each file (or group in composed mode)
   - Builds JSON schemas from type hints using Pydantic models
   - Registers functions with their signatures as MCP tools
   - Handles async/sync function differences automatically

3. **Architecture Configuration**
   - **Composed Mode**: Creates a main FastMCP host with all sub-instances mounted
     - Uses separators (+, _, .) for namespace management
     - Handles tool naming to prevent collisions
   - **Routed Mode**: Creates separate FastMCP instances with independent routes
     - Maps directory structure to URL paths
     - Maintains original function names within each module

4. **Transport & Protocol Implementation**
   - Implements JSON-RPC 2.0 for request/response
   - Supports both SSE streaming and JSON response formats
   - Optional event store for session persistence (SQLite-based)
   - Middleware for CORS, sessions, and other functionality

## 🔝️ Architecture Modes

The SDK supports two distinct architectural patterns that determine how your Python functions are exposed as MCP tools. Each mode offers different trade-offs between simplicity, scalability, and organization.

### 📋 Composed Mode (Recommended)

**Implementation Details**:
```python
# From application_factory.py
def _create_composed_application(mcp_instances, mcp_server_name, ...):
    # Create a main FastMCP instance as the host
    main_mcp = FastMCP(name=mcp_server_name)
    
    # Mount each file's FastMCP instance with prefixed tool names
    for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
        main_mcp.mount(
            route_path,
            file_mcp,
            as_proxy=False,
            resource_separator="+",
            tool_separator="_",
            prompt_separator=".",
        )
```

**Technical Benefits**:
- ✅ **Single ASGI Application**: All tools are handled by one Starlette app
- ✅ **Shared Session State**: Tools can share state within a session
- ✅ **Reduced Resource Overhead**: Only one FastMCP instance runs at the server level
- ✅ **Automatic Naming Convention**: Tools are prefixed with file name (e.g., `tool_math_add`)
- ✅ **Unified Authentication**: Apply auth to all tools at once

**Best for**:
- Applications requiring unified API access
- Tools that work together cooperatively
- Simplified client integration

**Usage**:
```bash
# Using composed mode (default)
mcp-modelservice run --source-path ./my_tools --mode composed

# Access: http://localhost:8080/mcp-server/mcp
# Tools: tool_file1_add, tool_file2_calculate, etc.
```

### 🔀 Routed Mode

**Implementation Details**:
```python
# From application_factory.py
def _create_routed_application(mcp_instances, mcp_service_base_path, ...):
    # For each file's FastMCP instance, create a separate route
    routes = []
    for file_path, (file_mcp, route_path, tools_registered) in mcp_instances.items():
        # Create an ASGI app for this instance
        instance_asgi_app = create_streamable_http_app(
            server=file_mcp,
            streamable_http_path=mcp_service_base_path,
            # Instance-specific configuration
        )
        # Mount this app at its own route path
        routes.append(Mount(route_path, app=instance_asgi_app))
        
    # Create main Starlette app with all routes
    app = Starlette(routes=routes, middleware=middleware)
```

**Technical Benefits**:
- ✅ **True Microservices**: Each module runs as an independent MCP server
- ✅ **Namespace Isolation**: Tools retain original names without prefixing
- ✅ **Selective Scaling**: Deploy and scale modules independently
- ✅ **Independent State**: No shared state between different modules
- ✅ **Clean URL Hierarchy**: Directory structure is directly reflected in URLs

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

### 🏆 Comprehensive Mode Comparison

| Feature | Composed Mode | Routed Mode |
|---------|---------------|-------------|
| **Architecture** | Monolithic | Microservices |
| **URL Structure** | `/mcp-server/mcp` (single endpoint) | `/math_tools/mcp`, `/text_tools/mcp` (multiple) |
| **Tool Naming** | Prefixed: `tool_file_function` | Original: `function` |
| **Session State** | Shared across all tools | Isolated per module |
| **Resource Usage** | Lower (single FastMCP instance) | Higher (multiple instances) |
| **Startup Time** | Faster (one application) | Slower (multiple applications) |
| **Memory Footprint** | Lower | Higher |
| **Deployment** | Single service | Can be deployed separately |
| **Scaling Strategy** | Vertical (scale up the service) | Horizontal (scale specific modules) |
| **Development Focus** | Feature-rich single service | Independent specialized modules |
| **Error Isolation** | Issues may affect all tools | Issues isolated to specific modules |
| **Authentication** | Apply once to all tools | Can configure per module |
| **Cross-Module Calls** | Direct (in same process) | Via HTTP (inter-process) |
| **Use Case** | Cohesive, related functionality | Distinct, separate domains |

### 🔄 When to Choose Each Mode

**Choose Composed Mode when**:
- You want a simple, unified API
- Your tools are logically related
- You need to minimize resource usage
- You prefer simplified deployment
- You have a single team managing all tools

**Choose Routed Mode when**:
- You need strong module isolation
- Different teams manage different modules
- You want fine-grained scaling control
- Your tools serve distinct domains
- You need independent versioning or deployment

## 🌐 Deployment Options

### Local Development
```bash
# Quick development with hot reload
mcp-modelservice run --source-path ./my_project --reload True

# Expose on all interfaces (for network testing)
mcp-modelservice run --source-path ./my_project --host 0.0.0.0 --port 9000

# With custom server name and service path
mcp-modelservice run --source-path ./my_project --mcp-name CustomTools --server-root /api
```

### Containerized Deployment

Create a `Dockerfile` for your packaged service:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy packaged service contents
COPY my-service/ .

# Install dependencies
RUN pip install --no-cache-dir -r project/requirements.txt

# Default command runs the service
CMD ["/bin/bash", "project/start.sh"]

# Expose service port
EXPOSE 8080
```

### Production Deployment Strategies

1. **ASGI Server with Uvicorn/Gunicorn**:
   - Your packaged `start.sh` already uses Uvicorn
   - For production, consider using Gunicorn as a process manager:
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker -w 4 main:app
   ```

2. **Kubernetes Deployment**:
   ```yaml
   # Sample Kubernetes deployment
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mcp-service
   spec:
     replicas: 3
     # ... other Kubernetes configuration
   ```

3. **Serverless Functions** (AWS Lambda, Google Cloud Functions):
   - Use Mangum for AWS Lambda adaptation:
   ```python
   from mangum import Mangum
   # ... create your MCP application
   handler = Mangum(app)  # Lambda entry point
   ```

## 📚 Client Integration

### Interactive Browser Interface

Every MCP service includes a built-in web interface for interactive testing:

1. Start your service:
   ```bash
   mcp-modelservice run --source-path ./my_project --port 8080
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8080/mcp-server/mcp
   ```
   
3. You'll see a user-friendly interface that allows you to:
   - Browse all available tools
   - Test tools with parameter forms
   - View JSON schema documentation
   - See execution results

### Python Client Examples

#### Direct HTTP Client (Standard Library)
```python
import json
import urllib.request

def call_mcp_tool(tool_name, params, endpoint="http://localhost:8080/mcp-server/mcp"):
    # Prepare JSON-RPC payload
    payload = {
        "jsonrpc": "2.0",
        "method": tool_name,
        "params": params,
        "id": 1
    }
    
    # Convert to bytes for request
    data = json.dumps(payload).encode('utf-8')
    
    # Create request with proper headers
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    
    # Send request and parse response
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

# Example usage with composition mode naming
result = call_mcp_tool("tool_math_tools_add", {"a": 10, "b": 5})
print(f"Result: {result['result']}")  # Result: 15
```

#### Requests Library Client
```python
import requests

def call_mcp_tool(tool_name, params, endpoint="http://localhost:8080/mcp-server/mcp"):
    response = requests.post(
        endpoint,
        json={
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params,
            "id": 1
        }
    )
    return response.json()

# Call a tool and handle errors
try:
    result = call_mcp_tool("tool_text_tools_word_count", {"text": "Hello MCP world!"})
    if 'error' in result:
        print(f"Error: {result['error']['message']}")
    else:
        print(f"Word count: {result['result']}")  # Word count: 3
except Exception as e:
    print(f"Request failed: {e}")
```

#### FastMCP Native Client (Async)
```python
import asyncio
from fastmcp import FastMCP

async def main():
    # Connect to the MCP service
    client = FastMCP("http://localhost:8080/mcp-server/mcp")
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {', '.join(t.id for t in tools)}")
    
    # Call a tool with parameters
    result = await client.call_tool("tool_math_tools_multiply", {"a": 4, "b": 7})
    print(f"4 × 7 = {result}")  # 4 × 7 = 28
    
    # Call another tool with the same client
    result = await client.call_tool("tool_text_tools_concatenate", 
                                   {"text1": "Hello ", "text2": "World!"})
    print(result)  # Hello World!

# Run the async example
asyncio.run(main())
```

### JavaScript/TypeScript Client
```typescript
async function callMcpTool(toolName: string, params: Record<string, any>) {
  const response = await fetch('http://localhost:8080/mcp-server/mcp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: toolName,
      params: params,
      id: 1,
    }),
  });

  return await response.json();
}

// Example usage
const result = await callMcpTool('tool_math_tools_add', { a: 3, b: 7 });
console.log(`The sum is: ${result.result}`);  // The sum is: 10
```

## ⚙️ Configuration

### Command Line Options

#### Common Options (for all commands)

| Option | Description | Default |
|--------|-------------|---------|
| `--source-path` | Path to Python files/directory | Current directory |
| `--log-level` | Logging level (debug, info, warning, error) | info |
| `--functions` | Comma-separated specific functions to expose | All discovered functions |
| `--mcp-name` | MCP server name | MCPModelService |
| `--server-root` | Root path for MCP service group | /mcp-server |
| `--mcp-base` | Base path for MCP protocol endpoints | /mcp |
| `--mode` | Architecture mode (composed/routed) | composed |
| `--cors-enabled` | Enable CORS middleware | True |
| `--cors-allow-origins` | Allowed CORS origins (comma-separated) | * (all origins) |

#### Run Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--host` | Network interface to bind | 127.0.0.1 |
| `--port` | Service port | 8080 |
| `--reload` | Enable auto-reload for development | False |
| `--workers` | Number of worker processes | 1 |
| `--enable-event-store` | Enable SQLite event store for persistence | False |
| `--event-store-path` | Path for event store database | ./mcp_event_store.db |
| `--stateless-http` | Enable stateless HTTP mode | False |
| `--json-response` | Use JSON response format instead of SSE | False |

#### Package Command Options

| Option | Description | Default |
|--------|-------------|---------|
| `--package-name` | Base name for output package | Required (no default) |
| `--package-host` | Host to configure in start script | 0.0.0.0 |
| `--package-port` | Port to configure in start script | 8080 |
| `--package-reload` | Enable auto-reload in packaged service | False |
| `--package-workers` | Number of workers in packaged service | 1 |
| `--mw-service` | ModelWhale service mode | True |

### Environment Variables Support

All configuration options can be specified via environment variables using the format `MCP_OPTION_NAME`:

```bash
# .env file example
MCP_HOST=0.0.0.0
MCP_PORT=9000
MCP_SERVER_NAME=production-mcp-service
MCP_LOG_LEVEL=INFO
MCP_CORS_ENABLED=true
MCP_CORS_ALLOW_ORIGINS=https://example.com,https://app.example.com
MCP_MODE=composed
MCP_ENABLE_EVENT_STORE=true
```

### Configuration Precedence

1. Command-line arguments (highest priority)
2. Environment variables
3. Default values (lowest priority)

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

- **GitHub Repository**: [https://github.com/modelcontextprotocol/mcpy-cli](https://github.com/modelcontextprotocol/mcpy-cli)
- **Full Documentation**: Available in the GitHub repository
- **Issue Tracking**: Report bugs and request features on GitHub
- **Community**: Join discussions and get help

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/modelcontextprotocol/mcpy-cli/blob/main/CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/modelcontextprotocol/mcpy-cli/blob/main/LICENSE) file for details.

---

**Made with ❤️ for the Python and MCP communities**

Ready to transform your Python functions into powerful MCP services? Install `mcpy-cli` today! 