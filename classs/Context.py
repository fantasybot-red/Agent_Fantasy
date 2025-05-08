from typing import List

from discord import Message, Embed
from classs import FClient


class Context:
    message: Message
    client: FClient
    embeds: List[Embed]
    extra_info: dict
    response: str

    def __init__(self, message: Message, client: FClient):
        self.message = message
        self.client = client
        self.response = ""
        self.embeds = []
        self.extra_info = {}

    def add_response(self, response: str):
        self.response += response
