import time
from typing import List

from discord import Message, Embed
from classs import FClient


class Context:
    message: Message
    client: FClient
    embeds: List[Embed]
    extra_info: dict
    response: str
    response_message: Message | None
    last_edit: int

    def __init__(self, message: Message, client: FClient):
        self.message = message
        self.client = client
        self.response = ""
        self.embeds = []
        self.extra_info = {}
        self.response_message = None
        self.last_edit = 0

    async def add_response(self, response: str):
        self.response += response
        if time.time() - self.last_edit > 3 and self.response.strip():
            temp_content = self.response + self.client.loading_emoji
            if self.response_message is None:
                self.response_message = await self.message.reply(temp_content, embeds=self.embeds)
            else:
                await self.response_message.edit(content=temp_content, embeds=self.embeds)
            self.last_edit = time.time()

    async def finish_response(self):
        if self.response_message is None:
            await self.message.reply(self.response, embeds=self.embeds)
        else:
            await self.response_message.edit(content=self.response, embeds=self.embeds)

    async def set_status(self, status: str):
        if self.response_message is None:
            await self.message.reply(status)
        else:
            await self.response_message.edit(content=status)
