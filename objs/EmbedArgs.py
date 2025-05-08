from typing import TypedDict, Optional, List


class EmbedField(TypedDict):
    name: str
    value: str
    inline: Optional[bool]


class EmbedAuthor(TypedDict):
    name: str
    url: Optional[str]
    icon_url: Optional[str]


class EmbedFooter(TypedDict):
    text: str
    icon_url: Optional[str]

class Image(TypedDict):
    url: str

class EmbedArgs(TypedDict):
    title: Optional[str]
    description: Optional[str]
    url: Optional[str]
    color: Optional[int]
    footer: Optional[EmbedFooter]
    fields: Optional[List[EmbedField]]
    author: Optional[EmbedAuthor]
    thumbnail: Optional[Image]
    image: Optional[Image]
