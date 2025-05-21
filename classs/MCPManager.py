import os
import traceback
from typing import Dict, Any, List
from mcp import ClientSession, Tool
from mcp.client.sse import sse_client

from classs.AIContext import AIContext

class MCPFunction:
    name: str

    def __init__(self, tool: Tool, client_name: str):
        self.name = tool.name
        self.description = tool.description
        self.inputSchema = tool.inputSchema
        self.client_name = client_name

    def to_dict(self):
        parameters = self.inputSchema.copy()
        parameters.pop("$schema", None)
        return {
                    "type": "function",
                    "function": {
                        "name": self.name,
                        "description": self.description,
                        "parameters": parameters
                    }
                }

    async def call(self, ctx: AIContext, **kwargs):
        """
        Call the function with the given context and arguments.
        """
        data = await ctx.mcp_session.call_tool(self, kwargs)
        raw_data = data.model_dump()
        content = []
        for message in raw_data["content"]:
            if message["type"] == "image":
                filename = ctx.add_temp_attachment(message["data"], message["mimeType"])
                content.append({
                    "type": "text",
                    "text": f"Image \"{filename}\" added to temporary attachments.",
                })
            else:
                content.append(message)
        return content


class MCPManager:
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
        for name, url in self.mcp_host.items():
            stream_client = sse_client(
                url=url
            )
            try:
                async with stream_client as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tool_list = await session.list_tools()
                        for tool in tool_list.tools:
                            if tool.name in functions:
                                raise EnvironmentError(
                                    f"Duplicate function name: {tool.name} host {name}. Please check your environment variables."
                                )
                            functions[tool.name] = MCPFunction(tool, name)
                print(f"Loaded {len(functions)} functions from {name}")
            except Exception:
                traceback.print_exc()
        return functions

    def create_session(self):
        """
        Create a new session for the given client.
        """
        return MCPSession(self)

class MCPSession:
    clients: Dict[str, List[ClientSession | Any]]

    def __init__(self, manager: MCPManager):
        self.manager = manager
        self.clients = {}

    async def get_client_session(self, name: str):
        if name in self.clients:
            return self.clients[name][0]
        url = self.manager.mcp_host[name]
        stream_client = sse_client(
            url=url
        )
        read, write = await stream_client.__aenter__()
        session = await ClientSession(read, write).__aenter__()
        await session.initialize()
        self.clients[name] = [session, stream_client]
        return session

    async def call_tool(self, function: MCPFunction, kwargs: dict):
        client = await self.get_client_session(function.client_name)
        try:
            data = await client.call_tool(function.name, kwargs)
            return data
        except Exception as e:
            traceback.print_exc()
            raise e

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        for transport, client in self.clients.values():
            await transport.__aexit__(exc_type, exc_val, exc_tb)
            await client.__aexit__(exc_type, exc_val, exc_tb)




