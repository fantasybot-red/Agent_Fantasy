import io
import textwrap
import traceback
from datetime import datetime
from typing import List, Literal
import discord
from contextlib import redirect_stdout
from classs import Module, tool, Context
from objs.EmbedArgs import EmbedArgs


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
                func = env["func"]
                try:
                    with redirect_stdout(stdout):
                        ret = await func()
                except Exception:
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
        embeds="list of embeds to add to the message max 10 embeds",
        content="content of the message when send with embed",
    )
    async def set_embeds(self, ctx: Context, embeds: List[EmbedArgs]):
        """
        Set embeds to the response message.
        - You shouldn't use embeds for usual text messages.
        - Mentions in embeds are not notified — use `content` to mention users.
        - The embed title supports **plain text only** — no markdown or mentions.
        - Always remember image link is not display inside embed content.
        - You need at least one embed to send a message.
        """
        if not len(embeds):
            return {"reason": "there are not embeds to set", "error": True}
        ctx.embeds.extend([discord.Embed.from_dict(embed) for embed in embeds])
        return {"error": False}

    @tool()
    def format_time(self, ctx: Context, time_text: str, type_time: Literal["t", "T", "d", "D", "F", "R"]=None):
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
        unix_time = datetime.fromisoformat(time_text).timestamp()
        return f"<t:{int(unix_time)}:{type_time}>" if type_time else f"<t:{int(unix_time)}>"


async def setup(client):
    await client.add_module(ContextSupport(client))
