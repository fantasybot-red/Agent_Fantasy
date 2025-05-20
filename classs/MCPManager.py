import os
import asyncio
import traceback
from typing import Dict

from mcp import ClientSession, Tool
from mcp.client.sse import sse_client


class MCPFunction:
    name: str
    client: ClientSession

    def __init__(self, client: ClientSession, tool: Tool):
        self.name = tool.name
        self.description = tool.description
        self.inputSchema = tool.inputSchema
        self.client = client

    def to_dict(self):
        parameters = self.inputSchema.copy()
        del parameters["$schema"]
        return {
                    "type": "function",
                    "function": {
                        "name": self.name,
                        "description": self.description,
                        "parameters": parameters
                    }
                }

    async def call(self, _ctx, **kwargs):
        """
        Call the function with the given context and arguments.
        """
        data = await self.client.call_tool(self.name, kwargs)
        return data.model_dump() # make data to dict and jsonable


class MCPManager:
    mcp_client: Dict[str, ClientSession] = {}
    mcp_host: Dict[str, str] = {}

    def __init__(self):
        self.mcp_host = {}
        for k, v in os.environ.items():
            if not k.startswith("MCP_"):
                continue
            name = k[4:].lower()
            if name not in self.mcp_host:
                self.mcp_host[name] = v
            else:
                raise EnvironmentError(
                    f"Duplicate MCP connection name: {name}. Please check your environment variables."
                )

    async def get_tools(self) -> list[MCPFunction]:
        functions = {}
        for name, client in self.mcp_client.items():
            tool_list = await client.list_tools()
            for tool in tool_list.tools:
                if tool.name in functions:
                    raise EnvironmentError(
                        f"Duplicate function name: {tool.name} host {name}. Please check your environment variables."
                    )
                functions[tool.name] = MCPFunction(client, tool)
        return functions

    async def init_mcp(self):
        for name, url in self.mcp_host.items():
            startup_event = asyncio.Event()
            asyncio.create_task(self.start_mcp(name, url, startup_event))
            await startup_event.wait()  # Wait for the startup event to be set

    async def start_mcp(self, name: str, url: str, startup_event: asyncio.Event):
        stream_client = sse_client(
            url=url
        )
        try:
            async with stream_client as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    startup_event.set()
                    self.mcp_client[name] = session
                    await asyncio.Event().wait()  # Keep the session alive
        except Exception:
            traceback.print_exc()
            startup_event.set() # Set the event even if there is an error to avoid deadlock

