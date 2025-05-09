import io
import textwrap
import traceback
from datetime import datetime
from typing import List, Callable
import discord
from contextlib import redirect_stdout
from classs import Module, tool, Context
from objs.EmbedArgs import EmbedArgs
from objs.Utilitys import TimeData


class ContextSupport(Module):

    @tool(
    f"""
        Read-only eval function for safely retrieving data from discord.py objects.
        - you are writing body for the function.
        - Access is **read-only** no modifications or side effects allowed.
        - Supported objects: `message` (discord.Message), `client` (discord.Client).
        - Safe to use `await`
        - No user or arbitrary code execution.
        - You need to add `return` at the end to get output.
        - Always handle possible `None` or empty values.
        - Use `client.fetch_user` to retrieve a user banner.
        
        Example:
        ```python
        return message.author.id
        ```
        discord.py version: {discord.__version__}
        """,
        body="python code to run",
    )
    async def get_extra_info(self, ctx: Context, body: str):
        try:
            env = {
                "message": ctx.message,
                "client": ctx.client
            }
            to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'
            stdout = io.StringIO()
            try:
                exec(to_compile, env)
                func: Callable = env["func"]
                try:
                    with redirect_stdout(stdout):
                        ret = await func()
                except BaseException:
                    value = stdout.getvalue()
                    out = value + traceback.format_exc()
                else:
                    value = stdout.getvalue()
                    out = value + str(ret) if ret is not None else value
                return {"log": out, "error": False}
            except Exception as e:
                return {"log": str(e), "error": True}
        except Exception as e:
            return {"log": str(e), "error": True}

    @tool(
        embeds="list of embeds",
        content="content of the message when send with embed",
    )
    async def set_embeds(self, ctx: Context, embeds: List[EmbedArgs]):
        """
        Set embeds to the response message.
        - You shouldn't use embeds for usual text messages.
        - Mentions in embeds are not notified — use `content` to mention users.
        - The embed title supports **plain text only** — no markdown or mentions.
        - Always remember image link is not display inside embed content.
        - Image link is not display inside embed content.
        - You MUST use `image` or `thumbnail` to display image link inside embed.
        - You need at least one embed to send a message.
        - You can set up to 10 embeds.
        """
        if not len(embeds):
            return {"reason": "there are not embeds to set", "success": False}
        if len(ctx.embeds) + len(embeds) > 10:
            return {"reason": "there are too many embeds to set", "success": False}
        ctx.embeds.extend([discord.Embed.from_dict(embed) for embed in embeds])
        return {"success": True, "embeds_count": len(ctx.embeds), "reason": f"{len(embeds)} embeds add successfully"}

    @tool()
    def format_time(self, ctx: Context, times: List[TimeData]):
        """
        Reformat in time in ISO 8601 with microseconds and offset to discord timestamp format.
        Use type_time for different format.
        default "type_time" example "20 April 2021 16:20"
        t: short time example "16:20"
        T: long time example "16:20:30"
        d: short date example "20/04/2021"
        D: long date example "20 April 2021"
        F: full date example "Tuesday, 20 April 2021 16:20"
        R: relative time example "2 months ago"
        """
        return_time = []
        for time_data in times:
            unix_time = datetime.fromisoformat(time_data["time_text"]).timestamp()
            type_time = time_data.get("type_time", None)
            return_time.append(f"<t:{int(unix_time)}:{type_time}>" if type_time else f"<t:{int(unix_time)}>")
        return return_time

    @tool(
        status="what you will do next",
    )
    async def set_status(self, ctx: Context, status: str):
        """
        Set status before sending the message.
        - You can set status to any text you want.
        - Status allow markdown and mentions.
        - Status must be short and clear.
        - You MUST set status if you think that user will wait for a long time.
        - You not allow to say tool name in status.
        - You don't need to set status if you're not using tool.
        """
        await ctx.set_status(status)
        return {"success": True, "reason": "status set successfully"}

async def setup(client):
    await client.add_module(ContextSupport(client))
