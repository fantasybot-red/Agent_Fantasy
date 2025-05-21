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
    voice_client: MusicPlayer
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
        self.attachments_update = False
        self.embeds_update = False

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
        return kwargs

    def add_temp_attachment(self, content: str, content_type: str):
        file_id = os.urandom(16).hex()
        file_ext = mimetypes.guess_extension(content_type) or ""
        filename = file_id+file_ext
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

    async def add_response(self, response: str):
        self._response += response
        if not self._response.strip():
            return
        if time.time() - self._last_edit > 3 and self._response.strip():
            temp_content = self._response + self.client.emojis["typing"]
            kwargs = self._gen_kwargs()
            await self._response_message.edit(content=temp_content, **kwargs)
            self._last_edit = time.time()

    async def start_response(self):
        self._response_message = await self.message.reply("-# " + self.client.emojis["typing"])

    async def finish_response(self):
        if not self._response.strip():
            return
        kwargs = self._gen_kwargs()
        await self._response_message.edit(content=self._response, **kwargs)

    async def set_status(self, status: str):
        status = self.client.emojis["loading"] + " " + status
        await self._response_message.edit(content=status)
