from discord import Message
from classs import FClient


class Context:
    message: Message
    client: FClient
    extra_info: dict = {}

    def __init__(self, message: Message, client: FClient):
        self.message = message
        self.client = client

    def __getattr__(self, item):
        attr = super().__getattribute__(item)
        if attr is None:
            return self.extra_info.get(item)
        return attr

    def __setattr__(self, key, value):
        if key in ["client", "message", "extra_info"]:
            super().__setattr__(key, value)
        else:
            self.extra_info[key] = value
