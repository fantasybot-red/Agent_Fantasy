import io
import textwrap
import traceback
from datetime import datetime
from typing import List, Callable
import discord
from contextlib import redirect_stdout
from classs import Module, tool, AIContext
from objs.EmbedArgs import EmbedArgs


class ContextSupport(Module):

    @tool(
        embeds="list of embeds",
        content="content of the message when send with embed",
    )
    async def set_embeds(self, ctx: AIContext, embeds: List[EmbedArgs]):
        """
        Set embeds to the response message.
        - You shouldn't use embeds for usual text messages.
        - Mentions in embeds are not notified — use normal response for that.
        - The embed title supports **plain text only** — no markdown or mentions.
        - Always remember image link is not display inside embed content.
        - Image link is not display inside embed content.
        - You MUST use `image` or `thumbnail` to display image link inside embed.
        - You need at least one embed to send a message.
        - You can set up to 10 embeds.
        - You Only Allow to set embeds 1 time.
        """
        if not len(embeds):
            return {"reason": "there are not embeds to set", "success": False}
        if len(embeds) > 10:
            return {"reason": "too many embeds to set", "success": False}
        if ctx.embeds:
            return {"reason": "embeds already set", "success": False}
        ctx.embeds = [discord.Embed.from_dict(embed) for embed in embeds]
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
        - You MUST use `set_status` before using tool except set data to the message.
        - You not allow to say tool name in status.
        - You don't need to set status if you're not using tool.
        """
        await ctx.set_status(status)
        return {"success": True, "reason": "status set successfully"}


async def setup(client):
    await client.add_module(ContextSupport(client))
