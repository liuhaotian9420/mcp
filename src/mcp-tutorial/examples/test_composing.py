# from fastapi import FastAPI
# from fastmcp import FastMCP
# from contextlib import asynccontextmanager
# import uvicorn
# from contextlib import asynccontextmanager, AsyncExitStack

# def make_combined_lifespan(*subapps):
#     """
#     Returns an asynccontextmanager suitable for FastAPI's `lifespan=…`
#     that will run all of the given subapps' lifespans in sequence.
#     """
#     @asynccontextmanager
#     async def lifespan(parent_app):
#         async with AsyncExitStack() as stack:
#             for subapp in subapps:
#                 # each subapp.lifespan is an async contextmanager expecting (parent_app)
#                 await stack.enter_async_context(subapp.router.lifespan_context(parent_app))
#             yield
#     return lifespan


# # 1) Define two FastMCP services in stateless-HTTP mode
# weather_mcp  = FastMCP(name="WeatherService",  stateless_http=True)
# calendar_mcp = FastMCP(name="CalendarService", stateless_http=True)

# @weather_mcp.tool()
# def get_forecast(city: str) -> dict:
#     return {"city": city, "forecast": "Sunny"}

# @calendar_mcp.tool()
# def add_event(title: str, date: str) -> str:
#     return f"Event '{title}' scheduled on {date}"

# # 2) Turn each into its own ASGI app (mounted at `/mcp` by default)
# weather_app  = weather_mcp.http_app(path="/mcp")
# calendar_app = calendar_mcp.http_app(path="/mcp")

# # 3) Combine their lifespan context managers

# # 4) Create one FastAPI parent with the combined lifespan…
# app = FastAPI(lifespan=make_combined_lifespan(weather_app, calendar_app))

# # 5) …and mount each sub-app on its own route
# app.mount("/mcp/weather",  weather_app)
# app.mount("/mcp/calendar", calendar_app)

# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)
from starlette.applications import Starlette
from starlette.routing      import Mount
from contextlib             import asynccontextmanager, AsyncExitStack
import uvicorn
from fastmcp                import FastMCP

# 1) Define two FastMCP services (stateless-HTTP mode)
weather_mcp  = FastMCP(name="WeatherService",  stateless_http=True)
calendar_mcp = FastMCP(name="CalendarService", stateless_http=True)

@weather_mcp.tool()
def get_forecast(city: str) -> dict:
    return {"city": city, "forecast": "Sunny"}

@calendar_mcp.tool()
def add_event(title: str, date: str) -> str:
    return f"Event '{title}' scheduled on {date}"

# 2) Turn each into its own Starlette sub-app at path="/mcp"
weather_app  = weather_mcp.http_app(path="/mcp")
calendar_app = calendar_mcp.http_app(path="/mcp")

# 3) Build a combined lifespan that enters each sub-app’s lifespan in turn
def make_combined_lifespan(*subapps):
    @asynccontextmanager
    async def lifespan(scope):
        async with AsyncExitStack() as stack:
            for sa in subapps:
                # each subapp has a .lifespan() async context manager
                await stack.enter_async_context(sa.router.lifespan_context(scope))
            yield
    return lifespan

# 4) Create one Starlette parent, mount each service, and wire lifespan
app = Starlette(
    debug=True,
    routes=[
        Mount("/mcp/weather",  app=weather_app),
        Mount("/mcp/calendar", app=calendar_app),
    ],
    lifespan=make_combined_lifespan(weather_app, calendar_app)
)

# 5) Run under Uvicorn as usual
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

