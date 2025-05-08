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
        Safe eval function for **read-only access** to `discord.py` objects.
        Always check function return can be None or empty.
        - Only use to **retrieve information** from the following objects:
          - `message`: discord.Message
          - `client`: discord.Client
        - Do **not** execute arbitrary user code.
        - `await` is allowed in this context.
        - discord.py version {discord.__version__} is used.
        - You need to use return to see the result or print it.
        - You can use message to get current message info or author info.
        - User Banner can only be retrieved with `client.fetch_user`.
        """,
        body="python code to run",
    )
    async def safe_eval(self, ctx: Context, body: str):
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
    async def send_embed(self, ctx: Context, embeds: List[EmbedArgs], content: str=None):
        """
        Send a message with an embed (if needed), following these rules:
        - Embeds must not be empty.
        - Use an embed **only** when displaying images or structured data (e.g., using fields).
        - Mentions in embeds are not notified — use `content` to mention users.
        - The embed title supports **plain text only** — no markdown or mentions.
        - Embeds dose **not** display images from URLs so use `thumbnail` or `image` for images.
        """
        if not len(embeds):
            return {"error": "embeds cannot be empty"}
        kwargs = {"embeds": [discord.Embed.from_dict(embed) for embed in embeds]}
        if content is not None:
            kwargs["content"] = content
        await ctx.message.reply(**kwargs)

    @tool()
    def reformat_time(self, ctx: Context, time_text: str, type_time: Literal["t", "T", "d", "D", "F", "R"]=None):
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
