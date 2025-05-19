from fastapi import FastAPI, Query
from fastapi_mcp import FastApiMCP
import requests
from pydantic import BaseModel, Extra
from typing import List, Dict, Any
import os
import logging


API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdPaWQiOiI2NWYyZjkzMDg4MGYzNjZlODZhMWM3MmEiLCJ1c2VyT2lkIjoiNjVmMmY5MTg4ODBmMzY2ZTg2YTFiYWVhIiwibmFtZSI6IjExIiwiaXNPcGVuQVBJIjp0cnVlLCJhcHAiOiJGbG93QXBwIiwiYXBwSWQiOiI2ODFjMWUzNzY5ODczMGExZDYzOGZkMmUiLCJpYXQiOjE3NDY2OTU2NTcsImlzcyI6Imh0dHBzOi8vZGV2LXY1ejZ4bjE4dXcubW9kZWx3aGFsZS5jb20ifQ.EO8TNxSB7WTnQAzoT6uddV9N10J48rSk0rVHiGzM1EM"
EXTERNAL_URL = "https://dev-v5z6xn18uw.modelwhale.com/v3/api/flow-apps/681c1e37698730a1d638fd2e/completions"
EXTERNAL_HEADER = {
    "X-kesci-user": "65f2f918880f366e86a1baea",
    "X-kesci-org": "65f2f930880f366e86a1c72a",
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
ROOT_PATH = os.getenv("root_path", "")

app = FastAPI(root_path=ROOT_PATH)


logger = logging.getLogger(__name__)


class NameValueItem(BaseModel):
    Name: str
    Value: Any

    class Config:
        # forbid any extra keys beyond Name and Value
        extra = Extra.forbid


class WorkflowInput(BaseModel):
    inputs: List[NameValueItem]


class WorkflowOutput(BaseModel):
    outputs: List[NameValueItem]


async def call_external_service(inputs: WorkflowInput):
    logger.info(f"Calling external service at {EXTERNAL_URL} with inputs: {inputs}")
    try:
        logger.debug(f"Inputs: {inputs}")
        logger.debug(f"data: {inputs.model_dump()}")
        response = requests.post(
            EXTERNAL_URL, headers=EXTERNAL_HEADER, json=inputs.model_dump()
        )
        response.raise_for_status()
        json_response = response.json()
        logger.info(f"Received response: {json_response}")

        outputs = json_response.get("data", {}).get("outputs", {})
        result = None
        if outputs:
            for k, v in outputs.items():
                if k.startswith("end-"):
                    result = v
                    break
        logger.info(f"Extracted result: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling external service: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing external service response: {e}")
        raise


@app.get("/", response_model=Dict[str, Any], operation_id="root", tags=["health"])
async def root():
    return {"message": "Hello World"}


@app.post("/call_workflow", operation_id="call_workflow", tags=["workflow"])
async def call_external_service_as_flow(
    workflow_input: WorkflowInput,
) -> Dict[str, Any]:
    """
    Receives workflow inputs, calls an external service, and returns the result.
    """
    try:
        result = await call_external_service(workflow_input)
        if result is not None:
            return {"status": "success", "result": result}
        else:
            return {
                "status": "success",
                "message": "Workflow completed, but no specific result found.",
            }
    except Exception as e:
        logger.error(f"Error in /call_workflow endpoint: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/call_agent", operation_id="call_agent", tags=["workflow"])
async def call_external_service_as_agent(
    workflow_input: WorkflowInput,
    max_retries: int = Query(
        ..., description='maximum retries should the workflow "fail"'
    ),
    try_count: int = Query(..., description="number of tries already used"),
) -> Dict[str, Any]:
    """
    Receives workflow inputs, but call the flow with extra parameters
    Args:
        workflow_input (WorkflowInput): _description_

    Returns:
        Dict[str, Any]: _description_
    """
    ...


mcp = FastApiMCP(
    app,
    name="Modelservice as mcp",
    description="provides workflow that adds up two numbers",
)
mcp.mount()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("modelservice_mcp_example:app", host="0.0.0.0", port=8080)
