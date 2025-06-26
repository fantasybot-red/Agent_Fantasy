import base64
import io
import mimetypes
import os
import time
from typing import List

import discord
from discord import Message, Embed, Member, User
from classs.MusicPlayer import MusicPlayer
from classs import FClient


class AIContext:
    message: Message
    voice_client: MusicPlayer | None
    client: FClient
    author: User | Member
    _response: str
    _response_message: Message
    _last_edit: int

    def __init__(self, message: Message, client: FClient):
        self.message = message
        self.author = message.author
        self.client = client
        self.voice_client = message.guild.voice_client
        self.mcp_session = client.mcp_manager.create_session()

        self._response = ""
        self._response_message = None
        self._last_edit = 0

        self.attachments = []
        self.cache_attachments = []
        self.embeds = []
        self.view = None
        self.view_update = False
        self.attachments_update = False
        self.embeds_update = False
        self.message_file = None

    async def __aenter__(self):
        await self.start_response()
        await self.mcp_session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.finish_response()
        await self.mcp_session.__aexit__(exc_type, exc_val, exc_tb)

    def _gen_kwargs(self):
        kwargs = {}
        if self.embeds_update:
            kwargs["embeds"] = self.embeds
            self.embeds_update = False
        if self.attachments_update:
            kwargs["attachments"] = self.attachments
            self.attachments_update = False
        if self.view_update:
            kwargs["view"] = self.view
            self.view_update = False
        return kwargs

    def add_temp_attachment(self, content: str, content_type: str):
        file_id = os.urandom(16).hex()
        file_ext = mimetypes.guess_extension(content_type) or ""
        filename = file_id + file_ext
        content = base64.b64decode(content)
        file = discord.File(io.BytesIO(content), filename=filename)
        self.cache_attachments.append(file)
        return filename

    def move_temp_attachments(self, filename: str):
        for attachment in self.cache_attachments:
            if attachment.filename == filename:
                self.attachments.append(attachment)
                self.cache_attachments.remove(attachment)
                self.attachments_update = True
                return attachment.filename
        return None

    def add_attachment(self, attachment: discord.File):
        self.attachments.append(attachment)
        self.attachments_update = True

    def set_embeds(self, embeds: List[Embed]):
        self.embeds.extend(embeds)
        self.embeds_update = True

    def set_view(self, view: discord.ui.View):
        self.view = view
        self.view_update = True

    async def add_response(self, response: str):
        self._response += response
        if not self._response.strip():
            return
        if time.time() - self._last_edit > 3 and self._response.strip():
            emoji = self.client.emojis["typing"]
            temp_content = self._response[:2000 - len(emoji)] + emoji
            kwargs = self._gen_kwargs()
            if len(self._response) > 2000:
                kwargs["attachments"] = kwargs.get("attachments", []) + [
                    discord.File(io.BytesIO(self._response.encode('utf-8')), filename="response.md",
                                 description="Full response content")
                ]
            await self._response_message.edit(content=temp_content, **kwargs)
            self._last_edit = time.time()

    async def start_response(self):
        if self._response_message is not None:
            return
        self._response_message = await self.message.reply("-# " + self.client.emojis["typing"])

    async def finish_response(self):
        if not self._response.strip():
            return
        kwargs = self._gen_kwargs()
        content = self._response
        if len(self._response) > 2000:
            kwargs["attachments"] = kwargs.get("attachments", []) + [
                discord.File(io.BytesIO(self._response.encode('utf-8')), filename="response.md",
                             description="Full response content")
            ]
            kwargs["content"] = self._response[:2000]
            content = self._response[:2000 - 3] + "..."
        await self._response_message.edit(content=content, **kwargs)

    async def set_status(self, status: str):
        status = self.client.emojis["loading"] + " " + status
        await self._response_message.edit(content=status)
