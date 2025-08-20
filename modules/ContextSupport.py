from typing import List
import discord
from classs import Module, tool
from classs.AIContext import AIContext
from objs.EmbedArgs import EmbedArgs


class ContextSupport(Module):

    @tool(
        filename="Name of file in temporary attachments",
    )
    async def move_temp_attachment(self, ctx: AIContext, filename: str):
        """
        Add file in temporary attachments to the message.
        - Temporary attachments are files that are not sent to the message.
        - Not all files in temporary should be sent to the message.
        """
        filename = ctx.move_temp_attachments(filename)
        if filename is None:
            return {"reason": "file not found in temporary attachments", "success": False}
        return {"success": True, "filename": filename, "reason": f"file {filename} moved to message successfully"}


async def setup(client):
    await client.add_module(ContextSupport(client))
