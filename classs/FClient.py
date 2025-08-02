import json
import os
import traceback
from typing import List
import base64
import aiohttp
import discord
from string import Template

from google_custom_search import CustomSearch, AiohttpAdapter

from classs.AIContext import AIContext
from openai import AsyncAzureOpenAI, BadRequestError, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall
from huggingface_hub import AsyncInferenceClient

from classs.MCPManager import MCPManager


class FClient(discord.Client):
    mcp_manager: MCPManager
    openai: AsyncAzureOpenAI | AsyncOpenAI
    huggingface: AsyncInferenceClient | None
    system_prompt: Template
    emojis: dict = {}
    functions = {}
    functions_json_schema = []
    google_search_client: CustomSearch = None

    def __init__(self, **options):
        intents = discord.Intents.all()
        self.load_open_ai(**options)
        self.load_huggingface()
        self.mcp_manager = MCPManager()
        with open("resources/system_prompt.md", "r", encoding="utf8") as f:
            self.system_prompt = Template(
                f.read()
            )
        for k, v in os.environ.items():
            if k.startswith("EMOJI_"):
                self.emojis[k[6:].lower()] = v
        allowed_mentions = discord.AllowedMentions.none()
        allowed_mentions.replied_user = True
        super().__init__(intents=intents, allowed_mentions=allowed_mentions)

    async def get_prompt(self, prompt_id: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://bin.mudfish.net/api/text/{prompt_id}") as response:
                if response.status == 200:
                    jdata_return = await response.json()
                    return base64.b64decode(jdata_return["text"]).decode()
                else:
                    return None

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

    def load_google_search(self):
        if os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
            self.google_search_client = CustomSearch(
                AiohttpAdapter(apikey=os.getenv('GOOGLE_API_KEY'), engine_id=os.getenv('GOOGLE_SEARCH_ENGINE_ID'))
            )
        else:
            self.google_search_client = None

    def load_huggingface(self):
        if os.getenv('HUGGINGFACE_TOKEN'):
            self.huggingface = AsyncInferenceClient(
                token=os.getenv('HUGGINGFACE_TOKEN')
            )
        else:
            self.huggingface = None

    def get_system_prompt(self, message: discord.Message, **kwargs):
        return self.system_prompt.safe_substitute(
            bot_mention=self.user.mention,
            bot_name=self.user.name,
            is_nsfw=message.channel.nsfw,
            channel_id=message.channel.id,
            channel_name=message.channel.name,
            **kwargs
        )

    async def process_stream_response(self, messages: List[ChatCompletionMessageParam], ctx: AIContext) -> (AIContext,                                                                                                  discord.Message):
        try:
            response = await self.openai.chat.completions.create(
                model=os.getenv('OPENAI_API_MODAL'),
                messages=messages,
                stream=True,
                tools=self.functions_json_schema,
                tool_choice="auto"
            )
        except BadRequestError as e:
            messages = [messages[0]]
            error_reason = e.response.json()["error"]["innererror"]["content_filter_result"]
            messages.append({
                "role": "system",
                "content": f"User just make you error following reason: {error_reason} \nRespond with a text message to fix this error."
            })
            return await self.process_stream_response(messages, ctx)
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
                                 messages: List[ChatCompletionMessageParam], ctx: AIContext):
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
                traceback.print_exc()
                result = {"error": str(e)}
                print(f"Tool call: {tool_call.function.name} with args: {args}, error: {e}")
            messages.append({
                "role": "tool",
                "content": result if isinstance(result, list) else json.dumps(result),
                "tool_call_id": tool_call.id,
            })
        return await self.process_stream_response(messages, ctx)

    async def get_messages_history(self, message: discord.Message):
        messages = [{
            "role": "user",
            "content": await  self.format_user_message(message)
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
                    "content": await self.format_user_message(msg)
                })
        messages.reverse()
        return messages

    async def format_user_message(self, message: discord.Message) -> str:
        context = {
            "User ID": message.author.id,
            "User Name": message.author.name,
            "Message ID": message.id
        }
        if isinstance(message.author, discord.Member):
            if message.author.nick:
                context["User Nickname"] = message.author.nick
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
        self.functions.update(await self.mcp_manager.get_tools())
        self.functions_json_schema.extend([f.to_dict() for f in self.functions.values()])
        self.load_google_search()  # Load Google Search client need event loop

    async def add_module(self, module):
        self.functions.update(module.functions)

    async def load_modules(self):
        for filename in os.listdir("modules"):
            if filename.endswith(".py"):
                module_name = filename[:-3]
                module = __import__(f"modules.{module_name}", fromlist=["setup"])
                await module.setup(self)
                print(f"Module {module_name} loaded successfully.")

    # EVENT HANDLER

    async def on_interaction(self, interaction: discord.Interaction):
        """Handle Discord interactions (buttons/select menus)."""
        # Only process component interactions (buttons, select menus)
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        # Handle prompt-related interactions
        if custom_id.startswith(("prompt:", "prompt_select:")):
            await self.handle_prompt_interaction(interaction, custom_id)

    async def handle_prompt_interaction(self, interaction: discord.Interaction, custom_id: str):
        is_select_menu = custom_id.startswith("prompt_select:")
        prompt_id = custom_id[14:] if is_select_menu else custom_id[7:]

        try:
            original_message = await interaction.channel.fetch_message(interaction.message.reference.message_id)
        except discord.NotFound:
            await interaction.response.send_message("Original message not found", ephemeral=True)
            return

        # reset user choices
        if is_select_menu:
            view = discord.ui.View.from_message(interaction.message, timeout=1)
            await interaction.response.edit_message(view=view)
        else:
            await interaction.response.defer()

        bot_prompt = await self.get_prompt(prompt_id)
        if not bot_prompt:
            await interaction.message.reply("Failed to retrieve prompt data", ephemeral=True)
            return
        
        ctx = AIContext(original_message, self)
        
        ctx._response_message = await interaction.message.reply(f"-# {self.emojis['typing']}")

        async with ctx:
            if is_select_menu:
                selected_values_raw = interaction.data.get("values", [])
                selected_values = [await self.get_prompt(value[3:]) for value in selected_values_raw if value.startswith("sl:")]
                bot_prompt = Template(bot_prompt).safe_substitute(values=selected_values)

        
            interaction_type = "menu" if is_select_menu else "button"
            user_info = {
                "User ID": interaction.user.id,
                "User Name": interaction.user.name
            }
            if isinstance(interaction.user, discord.Member):
                if interaction.user.nick:
                    user_info["User Nickname"] = interaction.user.nick

            messages = [
                {"role": "system", "content": self.get_system_prompt(original_message)},
                {"role": "user", "content": await self.format_user_message(original_message)},
                {"role": "assistant", "content": interaction.message.content},
                {"role": "developer", "content": [
                    {"type": "text", "text": f"User just selected a {interaction_type} with your note following reason: {bot_prompt}"},
                    {"type": "text", "text": f"User info: {json.dumps(user_info)}"}
                ]}
            ]

            await self.process_stream_response(messages, ctx)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.user not in message.mentions:
            return

        ctx = AIContext(message, self)
        async with ctx:
            messages = await self.get_messages_history(message)
            messages.insert(0, {
                "role": "system",
                "content": self.get_system_prompt(message)
            })

            await self.process_stream_response(
                messages,
                ctx
            )

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        pass
        # TODO: MAKE VOICE STATE HANDLER FOR NEW FEATURES

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
