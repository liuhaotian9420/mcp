"""
A demonstration on how an MCP client interacts with a MCP server.
"""
import requests
import json
import time


def main():
    print("MCP Client for testing FastApiMCP Arithmetic Service")
    print("Ensure fastapi_mcp_example.py is running.")

    # The FastAPI MCP example runs at http://localhost:8080
    # and FastApiMCP mounts its endpoint at /mcp by default.
    base_url = "http://localhost:8080/mcp/"
    print(f"Attempting to connect to MCP service at: {base_url}")

    session_id = None
    messages_url = None

    try:
        # Step 1: Establish SSE connection and get session_id
        # FastApiMCP typically returns the session_id in the event stream comments or headers.
        # This client uses a simplified GET that might get it from a Location header if redirected,
        # or attempts to parse from initial SSE comment events.
        print("\n--- Step 1: Establishing session ---")
        response = requests.get(base_url, stream=True)  # stream=True for SSE
        response.raise_for_status()  # Ensure we connected successfully

        # Attempt to get session_id from SSE comments (common for FastMCP)
        # A more robust client would continuously read the SSE stream here.
        # For this example, we'll just check the first few lines.
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith(": session_id="):
                session_id = line.split("session_id=")[1].strip()
                print(f"Extracted session_id from SSE comment: {session_id}")
                break
            elif "session_id=" in line:  # Fallback for other forms
                try:
                    # Example: data: {\"type\":\"mcp-event\",\"name\":\"session\",\"data\":{\"id\":\"xxxx\"}}
                    # Or other non-standard ways it might appear in initial burst
                    if "data:" in line and "session" in line and "id" in line:
                        payload_str = line.split("data: ", 1)[1]
                        payload_json = json.loads(payload_str)
                        if payload_json.get("data", {}).get("id"):
                            session_id = payload_json["data"]["id"]
                            print(
                                f"Extracted session_id from SSE data event: {session_id}"
                            )
                            break
                except Exception as e:
                    print(f"Could not parse line for session_id: {line}, error: {e}")
            if session_id:
                break  # Found it

        if not session_id:
            # Fallback: check headers if the server uses redirection (less common for SSE directly)
            if "Location" in response.headers:
                location = response.headers["Location"]
                if "session_id=" in location:
                    session_id = location.split("session_id=")[1].split("&")[0]
                    print(f"Extracted session_id from Location header: {session_id}")

        if not session_id:
            print("Could not automatically extract session ID.")
            print(
                "Please inspect the server output or use browser developer tools to find the session ID."
            )
            print("Then, manually provide it or adjust the client's extraction logic.")
            # For demonstration, let's ask the user or use a placeholder if interactive is hard
            # In a real script, you might raise an error or have a config.
            session_id = input("Enter session_id manually (or press Enter to abort): ")
            if not session_id:
                print("Aborting due to missing session_id.")
                return

        print(f"Using session ID: {session_id}")
        messages_url = f"{base_url}messages?session_id={session_id}"  # Corrected query param syntax

        # Step 2: Send initialize request
        print("\n--- Step 2: Sending initialize request ---")
        init_payload = {
            "jsonrpc": "2.0",
            "id": "init-123",  # Changed ID for uniqueness
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",  # Use a current or supported version
                "clientInfo": {"name": "TutorialMCPClient", "version": "0.2.0"},
                "capabilities": {
                    # "experimental": {}, # Optional
                    "tools": {
                        "listChanged": False  # Assuming we don't need dynamic tool list updates
                    }
                },
            },
        }

        init_response = requests.post(messages_url, json=init_payload)
        print(f"Initialize Response Status: {init_response.status_code}")
        try:
            print(
                f"Initialize Response Body: {init_response.json()}"
            )  # Try to print as JSON
            init_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        except (json.JSONDecodeError, requests.exceptions.HTTPError) as e:
            print(f"Error processing initialize response: {e}")
            print(f"Raw response: {init_response.text}")
            return

        # Step 3: Send notification/initialized
        print("\n--- Step 3: Sending notification/initialized ---")
        notify_payload = {"jsonrpc": "2.0", "method": "notification/initialized"}
        notify_response = requests.post(messages_url, json=notify_payload)
        print(f"Notification Response Status: {notify_response.status_code}")
        try:
            # Notifications might not have a body or might return 204 No Content
            if notify_response.text:
                print(f"Notification Response Body: {notify_response.json()}")
            notify_response.raise_for_status()
        except (json.JSONDecodeError, requests.exceptions.HTTPError) as e:
            print(f"Error processing notification response: {e}")
            print(f"Raw response: {notify_response.text}")
            # Non-critical for this example, so we might continue

        print("Waiting 2 seconds for server to process initialization...")
        time.sleep(2)

        # Step 4: Send tools/list request
        print("\n--- Step 4: Listing available tools ---")
        tools_list_payload = {
            "jsonrpc": "2.0",
            "id": "tools-list-456",  # Changed ID
            "method": "tools/list",
            "params": {},
        }
        tools_response = requests.post(messages_url, json=tools_list_payload)
        print(f"Tools List Response Status: {tools_response.status_code}")
        try:
            tools_data = tools_response.json()
            print(f"Tools List Response Body: {json.dumps(tools_data, indent=2)}")
            tools_response.raise_for_status()

            # Extract tool names for potential use
            available_tools = [
                tool["name"] for tool in tools_data.get("result", {}).get("tools", [])
            ]
            print(f"Available tools: {available_tools}")

        except (json.JSONDecodeError, requests.exceptions.HTTPError) as e:
            print(f"Error processing tools/list response: {e}")
            print(f"Raw response: {tools_response.text}")
            return

        # Step 5: Execute a tool (e.g., 'add')
        # The 'add' tool is derived from the /add POST endpoint in fastapi_mcp_example.py
        # It expects parameters 'a' and 'b'.
        print("\n--- Step 5: Executing the 'add' tool ---")
        tool_execute_payload = {
            "jsonrpc": "2.0",
            "id": "execute-add-789",
            "method": "tools/execute",
            "params": {
                "name": "add",  # This should match the operation_id or derived name
                "arguments": {"a": 15.5, "b": 4.5},
            },
        }
        execute_response = requests.post(messages_url, json=tool_execute_payload)
        print(f"Execute 'add' Tool Response Status: {execute_response.status_code}")
        try:
            execute_data = execute_response.json()
            print(
                f"Execute 'add' Tool Response Body: {json.dumps(execute_data, indent=2)}"
            )
            execute_response.raise_for_status()
            # The result of the add operation should be in execute_data['result']['return']
            if execute_data.get("result", {}).get("return") is not None:
                print(f"Result of add(15.5, 4.5): {execute_data['result']['return']}")
        except (json.JSONDecodeError, requests.exceptions.HTTPError) as e:
            print(f"Error processing tool execute response: {e}")
            print(f"Raw response: {execute_response.text}")
            return

        print("\nClient finished.")

    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        print(
            "Is the MCP server (fastapi_mcp_example.py) running at the specified base_url?"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Close SSE stream if it was kept open
        if "response" in locals() and hasattr(response, "close"):
            response.close()
            print("SSE connection closed.")


if __name__ == "__main__":
    main()
