import json
import os
import time
from typing import List

import discord
from string import Template
from .Context import Context
from openai import AsyncAzureOpenAI, BadRequestError, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall


class FClient(discord.Client):
    openai: AsyncAzureOpenAI | AsyncOpenAI
    system_prompt: Template
    emojis: dict = {}
    functions = {}
    functions_json_schema = []

    def __init__(self, **options):
        intents = discord.Intents.all()
        self.load_open_ai(**options)
        with open("resources/system_prompt.txt", "r") as f:
            self.system_prompt = Template(
                f.read()
            )
        for k, v in os.environ.items():
            if k.startswith("EMOJI_"):
                self.emojis[k[6:].lower()] = v
        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True
        super().__init__(intents=intents, allowed_mentions=allowed_mentions)

    def load_open_ai(self, **options):
        if os.getenv('OPENAI_API_TYPE') == 'AZURE_OPENAI':
            self.openai = AsyncAzureOpenAI(
                azure_deployment=os.getenv('OPENAI_API_MODAL'),
                **options
            )
        elif os.getenv('OPENAI_API_TYPE') == 'OPENAI':
            self.openai = AsyncOpenAI(
                **options
            )

    def get_system_prompt(self, message: discord.Message, **kwargs):
        return self.system_prompt.safe_substitute(
            bot_mention=self.user.mention,
            bot_name=self.user.name,
            is_nsfw=message.channel.nsfw,
            channel_id=message.channel.id,
            channel_name=message.channel.name,
            **kwargs
        )

    async def process_stream_response(self, messages: List[ChatCompletionMessageParam], ctx: Context) -> (str, discord.Message):
        try:
            response = await self.openai.chat.completions.create(
                model=os.getenv('OPENAI_API_MODAL'),
                messages=messages,
                stream=True,
                tools=self.functions_json_schema,
                tool_choice="auto"
            )
        except BadRequestError as e:
            return f"Error: {e}", None
        tool_calls = []
        message_response = None
        async for chunk in response:
            for choice in chunk.choices:
                if choice.delta.tool_calls is not None:
                    for tool_call in choice.delta.tool_calls:
                        if tool_call.id:
                            tool_calls.append(tool_call)
                        else:
                            tool_calls[-1].function.arguments += tool_call.function.arguments
                elif choice.delta.content is not None:
                    await ctx.add_response(choice.delta.content)
        if tool_calls:
            return await self.process_tool_calls(tool_calls, messages, ctx)
        return ctx, message_response

    async def process_tool_calls(self, tool_calls: List[ChoiceDeltaToolCall],
                                 messages: List[ChatCompletionMessageParam], ctx: Context):
        messages.append({
            "role": "assistant",
            "tool_calls": [tool.to_dict() for tool in tool_calls]
        })
        for tool_call in tool_calls:
            fn = self.functions.get(tool_call.function.name)
            if fn is None:
                messages.append({
                    "role": "tool",
                    "content": f"Tool '{tool_call.function.name}' not found.",
                    "tool_call_id": tool_call.id,
                })
                continue
            args = json.loads(tool_call.function.arguments)
            try:
                result = await fn.call(ctx, **args)
                print(f"Tool call: {tool_call.function.name} with args: {args}, result: {result}")
            except Exception as e:
                result = {"error": str(e)}
                print(f"Tool call: {tool_call.function.name} with args: {args}, error: {e}")
            messages.append({
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            })
        return await self.process_stream_response(messages, ctx)

    async def get_messages_history(self, message: discord.Message):
        messages = [{
            "role": "user",
            "content": await  self.fomart_user_message(message)
        }]
        async for msg in message.channel.history(limit=10, before=message):
            if msg.author == self.user:
                messages.append({
                    "role": "assistant",
                    "content": msg.content
                })
            elif not msg.author.bot:
                messages.append({
                    "role": "user",
                    "content": await self.fomart_user_message(msg)
                })
        messages.reverse()
        return messages

    async def fomart_user_message(self, message: discord.Message) -> str:
        context = {
            "User ID": message.author.id,
            "User Name": message.author.name
        }
        if message.author.nick:
            context["User Nickname"] = message.author.nick
            context["Message ID"] = message.id
        if message.reference:
            try:
                reply_message = await message.channel.fetch_message(message.reference.message_id)
                context["Message Reply Message ID"] = message.reference.message_id
                context["Message Reply Author"] = reply_message.author.name
                context["Message Reply Author ID"] = reply_message.author.id
                context["Message Reply Content"] = reply_message.content
            except discord.NotFound:
                pass
        context_string = '\n'.join([f'{k}: {v}' for k, v in context.items()])
        return f"{message.content}\n\n===============\n{context_string}"

    async def setup_hook(self) -> None:
        await self.load_modules()
        self.functions_json_schema.extend([f.to_dict() for f in self.functions.values()])

    async def add_module(self, module):
        self.functions.update(module.functions)

    async def load_modules(self):
        for filename in os.listdir("modules"):
            if filename.endswith(".py"):
                module_name = filename[:-3]
                module = __import__(f"modules.{module_name}", fromlist=["setup"])
                await module.setup(self)
