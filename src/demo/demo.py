# service.py

import os
from typing import Any, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP

# ---- 1) Define your request model ----


class InputPair(BaseModel):
    Name: str
    Value: Any


class CompletionRequest(BaseModel):
    inputs: List[InputPair]


# add logger
# import logging

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler('mcp_service.log')
#     ]
# )
# logger = logging.getLogger(__name__)


# ---- 2) Build the FastAPI app & endpoint ----

ROOT_PATH = os.getenv("root_path", "")

app = FastAPI(
    title="ModelWhale MCP Proxy",
    description="MCP tool proxying ModelWhale /completions",
    root_path=ROOT_PATH,
)

# Load your ModelWhale API key from the environment
# MODELWHALE_API_KEY = os.getenv("MODELWHALE_API_KEY")
MODELWHALE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2NWYyZjkzMDg4MGYzNjZlODZhMWM3MmEiLCJ1c2VyT2lkIjoiNjVmMmY5MTg4ODBmMzY2ZTg2YTFiYWVhIiwibmFtZSI6ImFhYSIsImlzT3BlbkFQSSI6dHJ1ZSwiYXBwIjoiRmxvd0FwcCIsImFwcElkIjoiNjgyMjhlZTI2YjFiZmM2OTNmYzRhMjM4IiwiaWF0IjoxNzQ3MTAyODYwLCJpc3MiOiJodHRwczovL2Rldi12NXo2eG4xOHV3Lm1vZGVsd2hhbGUuY29tIn0.FvOPdrVfa4gF0M7C7wrP8pbDqnNrPsaxYNJdkKoHDZQ"
if not MODELWHALE_API_KEY:
    raise RuntimeError("Please set MODELWHALE_API_KEY in your environment")


@app.post(
    "/modelwhale/completions",
    operation_id="modelwhale_completions",
    summary="Proxy to ModelWhale Completions API",
)
async def modelwhale_completions(req: CompletionRequest):
    url = (
        "https://dev-v5z6xn18uw.modelwhale.com"
        "/v3/api/flow-apps/68228ee26b1bfc693fc4a238/completions"
    )
    headers = {
        "X-kesci-user": "65f2f918880f366e86a1baea",
        "X-kesci-org": "65f2f930880f366e86a1c72a",
        "Authorization": f"Bearer {MODELWHALE_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=req.model_dump(), headers=headers)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code, detail=f"ModelWhale error: {resp.text}"
            )
        return resp.json()


# ---- 3) Create & configure your custom HTTP client ----

# Use a 5-minute (300s) timeout on all requests and point it at your app


# ---- 3) Mount the MCP server ----

mcp = FastApiMCP(
    app,
    http_client=httpx.AsyncClient(base_url="http://localhost:8080", timeout=300.0),
    name="ModelWhale Completions",
    description="Expose the ModelWhale completions endpoint as an MCP tool",
    # Make sure your app is reachable at http://localhost:8080
)
mcp.mount()  # <-- now all your FastAPI routes (including the proxy above) become MCP tools


# ---- 4) Run locally with: uvicorn service:app --reload ----

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
