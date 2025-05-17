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
    embeds: List[Embed]
    _response: str
    _response_message: Message
    _last_edit: int

    def __init__(self, message: Message, client: FClient):
        self.message = message
        self.author = message.author
        self.voice_client = message.guild.voice_client
        self.client = client
        self._response = ""
        self.attachments = []
        self.embeds = []
        self._response_message = None
        self._last_edit = 0
        self.attachments_update = False
        self.embeds_update = False

    def _gen_kwargs(self):
        kwargs = {}
        if self.embeds_update:
            kwargs["embeds"] = self.embeds
            self.embeds_update = False
        if self.attachments_update:
            kwargs["attachments"] = self.attachments
            self.attachments_update = False
        return kwargs

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
