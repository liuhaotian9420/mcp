"""
Configuration management for the CLI.
"""

from typing import Optional, List


class CommonOptions:
    """Common configuration options shared across CLI commands."""

    def __init__(
        self,
        source_path: Optional[str],
        log_level: str = "info",
        mode: str = "composed",
        functions: Optional[List[str]] = None,
        mcp_name: str = "MCPModelService",
        server_root: str = "/mcp-server",
        mcp_base: str = "/mcp",
        cors_enabled: bool = True,
        cors_allow_origins: Optional[List[str]] = None,
        enable_event_store: bool = False,
        event_store_path: Optional[str] = None,
        stateless_http: bool = False,
        json_response: bool = False,
        legacy_sse: bool = False,
    ):
        self.source_path = source_path
        self.log_level = log_level
        self.functions = functions
        self.mcp_name = mcp_name
        self.server_root = server_root
        self.mcp_base = mcp_base
        self.cors_enabled = cors_enabled
        self.cors_allow_origins = cors_allow_origins
        self.mode = mode
        self.enable_event_store = enable_event_store
        self.event_store_path = event_store_path
        self.stateless_http = stateless_http
        self.json_response = json_response
        self.legacy_sse = legacy_sse


def process_optional_list_str_option(
    opt_list: Optional[List[str]],
) -> Optional[List[str]]:
    """
    Process optional list string options from CLI, handling comma-separated values.

    Args:
        opt_list: Optional list of strings from CLI

    Returns:
        Processed list or None
    """
    if not opt_list:
        return None
    if len(opt_list) == 1 and "," in opt_list[0]:
        return [item.strip() for item in opt_list[0].split(",") if item.strip()]
    return [item.strip() for item in opt_list if item.strip()]
