from typing import List
import discord
from classs import Module, tool
from classs.AIContext import AIContext
from objs.EmbedArgs import EmbedArgs


class ContextSupport(Module):

    @tool(
        embeds="list of embeds"
    )
    async def set_embeds(self, ctx: AIContext, embeds: List[EmbedArgs]):
        """
        Set embeds to the response message.
        Embed Usage Guidelines:
        - Always include at least one embed in the response.
        - Use embeds for long replies like summaries or detailed content.
        - Do not repeat embed content in the message text.
        - Split long content across up to 10 embeds if needed.
        - Embed titles allow plain text only (no mentions or markdown).
        - Use normal message text to mention users if notification is needed.
        - To display an image, use the 'image' or 'thumbnail' (URLs in content won’t show images).
        - You only have one chance to set embeds.
        """

        if not len(embeds):
            return {"reason": "there are not embeds to set", "success": False}
        if len(embeds) > 10:
            return {"reason": "too many embeds to set", "success": False}
        if ctx.embeds:
            return {"reason": "embeds already set", "success": False}
        ctx.set_embeds([discord.Embed.from_dict(embed) for embed in embeds])
        return {"success": True, "embeds_count": len(ctx.embeds), "reason": f"{len(embeds)} embeds add successfully"}

    @tool(
        status="what you will do next",
    )
    async def set_status(self, ctx: AIContext, status: str):
        """
        Set status what you're doing if you're using tool.
        - You can use status to show what you're doing if you're using tool.
        - Status allow markdown and mentions.
        - Status must be short and clear.
        - Status should be less than 100 characters or more but not too long.
        - You MUST use `set_status` before using tool except set data to the message.
        - You not allow to say tool name in status.
        - You don't need to set status if you're not using tool.
        """
        await ctx.set_status(status)
        return {"success": True, "reason": "status set successfully"}

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
