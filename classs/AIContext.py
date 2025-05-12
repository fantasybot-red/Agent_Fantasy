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
    _response_message: Message | None
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
        self.attachments_check = False

    async def add_attachment(self, attachment: discord.File):
        self.attachments.append(attachment)
        self.attachments_check = True

    async def add_response(self, response: str):
        self._response += response
        if not self._response.strip():
            return
        if time.time() - self._last_edit > 3 and self._response.strip():
            temp_content = self._response + self.client.emojis["typing"]
            if self._response_message is None:
                if self.attachments_check:
                    self._response_message = await self.message.reply(temp_content, embeds=self.embeds, files=self.attachments)
                    self.attachments_check = False
                else:
                    self._response_message = await self.message.reply(temp_content, embeds=self.embeds)
            else:
                if self.attachments_check:
                    await self._response_message.edit(content=temp_content, embeds=self.embeds, attachments=self.attachments)
                    self.attachments_check = False
                else:
                    await self._response_message.edit(content=temp_content, embeds=self.embeds)
            self._last_edit = time.time()

    async def start_response(self):
        if self._response_message is None:
            self._response_message = await self.message.reply("-# " + self.client.emojis["typing"])
        else:
            await self._response_message.edit(content="-# " + self.client.emojis["typing"])

    async def finish_response(self):
        if not self._response.strip():
            return
        if self._response_message is None:
            await self.message.reply(self._response, embeds=self.embeds)
        else:
            await self._response_message.edit(content=self._response, embeds=self.embeds)

    async def set_status(self, status: str):
        status = self.client.emojis["loading"] + " " + status
        if self._response_message is None:
            self._response_message = await self.message.reply(status)
        else:
            await self._response_message.edit(content=status)