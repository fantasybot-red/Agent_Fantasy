import re
from typing import Union, List, Any, Optional
import discord
from discord import ui
from discord.ui import view
from classs import FClient


class FormatMessages:
    # IT WORKS LIKE A CHARM, DO NOT TOUCH IT ORDER MATTER
    COMPONENTS_REGEX = [
        ("Container", r'\[#Container#\]', r'\[/Container/\]'),
        ("MediaGallery", r'\[#MediaGallery#\]', r'\[/MediaGallery/\]'),
        ("ActionRow", r'\[#ActionRow#\]', r'\[/ActionRow/\]'),

        ("SectionThumbnail", r'\[#SectionThumbnail#([^\]]*)\]\(thn\|([^\|]+)\|([01])\)', r'\[/Section/\]'),
        ("SectionButtonLink", r'\[#SectionButton#([^\]]+)\]\(btu\|([^)]+)\)', r'\[/Section/\]'),
        ("SectionButton", r'\[#SectionButton#([^\]]+)\]\(bts\|([^\|]+)\|([01])\)', r'\[/Section/\]'),

        ("MediaGalleryItem", r'\[([^\]]*)\]\(media\|([^\|]+)\|([01])\)', None),
        ("Select", r'\[([^\]]+)\]\(st\|([^\|]+)\|([1-9])\|([1-9])\|([01])\)', None),
        ("ButtonLink", r'\[([^\]]+)\]\(btu\|([^)]+)\)', None),
        ("Button", r'\[([^\]]+)\]\(bts\|([^\|]+)\|([01])\)', None),
        ("Separator", r"\[#Separator#([12])\]", None)
    ]


    client: FClient

    def __init__(self, client: FClient):
        self.client = client

    async def format_ai_message(self, message: discord.Message) -> str:

        if message.author.id != self.client.user.id:
            return message.content  # Not by us by other bot, return content only

        elif not message.flags.components_v2:
            return message.content  # No components, return content only ( support old messages )

        component = ui.LayoutView.from_message(message, timeout=1)
        return self.component_to_text(component)

    def component_to_text(self, component: Union[ui.Item, view.BaseView]) -> str:
        content = ""
        if isinstance(component, ui.LayoutView):
            for item in component.children:
                content += self.component_to_text(item)

        elif isinstance(component, ui.TextDisplay):
            content += component.content

        elif isinstance(component, ui.Button):
            is_url_button = component.url is not None
            if is_url_button:
                content += f"[{component.label}](btu|{component.url})"
            else:
                content += f"[{component.label}](bts|{component.style}|{int(component.disabled)}|{component.custom_id}\)"

        elif isinstance(component, ui.Select):
            options_text = ','.join([opt.label for opt in component.options])
            content += f"[{component.placeholder}](st|{options_text}|{int(component.disabled)}|{component.custom_id}\)"

        elif isinstance(component, ui.ActionRow):
            if len(component.children) == 1 and isinstance(component.children[0], ui.Select):
                content += self.component_to_text(component.children[0]) # Select in ActionRow
            else:
                content += "[#ActionRow#]\n"
                for item in component.children:
                    content += self.component_to_text(item)
                content += "[/ActionRow/]\n"
        elif isinstance(component, ui.Container):
            content += "[#Container#]\n"
            for item in component.children:
                content += self.component_to_text(item)
            content += "[/Container/]\n"

        elif isinstance(component, ui.MediaGallery):
            content += "[#MediaGallery#]\n"
            for item in component.items:
                media = item.media
                content += f"[{media.placeholder}](media|{media.url}|{int(item.spoiler)})\n"
            content += "[/MediaGallery/]\n"

        elif isinstance(component, ui.Section):
            accessory = component.accessory
            # TODO: handle accessory

            if isinstance(accessory, ui.Thumbnail):
                content += f"[#SectionThumbnail#](thumbnail|{accessory.media.url}|{int(accessory.spoiler)})\n"
            elif isinstance(accessory, ui.Button):
                is_url_button = accessory.url is not None
                if is_url_button:
                    content += f"[#SectionButton#{accessory.label}](btu|{accessory.url})\n"
                else:
                    content += f"[#SectionButton#{accessory.label}](bts|{accessory.style}|{int(accessory.disabled)}|{accessory.custom_id}\)"
            for item in component.children:
                content += self.component_to_text(item)
            content += "[/Section/]\n"
        elif isinstance(component, ui.Separator):
            # 1 = small, 2 = large
            size = component.spacing.value
            content += f"[#Separator#{size}]\n"
        return content

    def regex_chuck_component(self, text: str) -> List[Any]:
        text_arr = []
        text_left = text.strip()

        while text_left:
            best_match = None
            best_name = None
            best_end_pattern = None

            for name, start_pattern, end_pattern in self.COMPONENTS_REGEX:
                if end_pattern is not None:
                    pattern = re.compile(f"{start_pattern}(.*?){end_pattern}", re.DOTALL)
                else:
                    pattern = re.compile(start_pattern, re.DOTALL)

                match = pattern.search(text_left)
                if match:
                    if best_match is None or match.start() < best_match.start():
                        best_match = match
                        best_name = name
                        best_end_pattern = end_pattern

            if best_match:
                start = best_match.start()
                end = best_match.end()

                if start > 0:
                    pre_text = text_left[:start].strip()
                    if pre_text:
                        text_arr.append(pre_text)

                sub_component, data = self.component_process_regex(
                    best_name, best_match, best_end_pattern is not None
                )

                if best_end_pattern is not None:
                    text_arr.append({"type": best_name, "component": sub_component, "data": data})
                else:
                    text_arr.append({"type": best_name, "data": data})

                text_left = text_left[end:].strip()
            else:
                if text_left:
                    text_arr.append(text_left)
                break

        return [x for x in text_arr if x]


    def component_process_regex(self, name: str, content: re.Match, end: bool):
        content_text = list(content.groups())[-1]
        data = {}
        if name == "SectionThumbnail":
            data = {
                "description": content.group(1),
                "url": content.group(2),
                "spoiler": bool(int(content.group(3)))
            }
        elif name == "SectionButtonLink":
            data = {
                "label": content.group(1),
                "content": content.group(2)
            }
        elif name == "SectionButton":
            data = {
                "label": content.group(1),
                "disabled": bool(int(content.group(3))),
                "content": content.group(4) if content.group(4) else None
            }
        elif name == "MediaGalleryItem":
            data = {
                "description": content.group(1),
                "url": content.group(2),
                "spoiler": bool(int(content.group(3)))
            }
        elif name == "ButtonLink":
            data = {
                "label": content.group(1),
                "url": content.group(2)
            }
        elif name == "Button":
            data = {
                "label": content.group(1),
                "style": content.group(2),
                "disabled": bool(int(content.group(3)))
            }
        elif name == "Select":
            data = {
                "placeholder": content.group(1),
                "options": content.group(2).split(',') if content.group(2) else [],
                "min": int(content.group(3)),
                "max": int(content.group(4)),
                "disabled": bool(int(content.group(5)))
            }
        elif name == "Separator":
            data = {
                "size": int(content.group(1)) if content.group(1) else 1
            }
        if end:
            return self.regex_chuck_component(content_text), data
        else:
            return None, data

    def text_to_component(self, text: str) -> ui.LayoutView:
        view = ui.LayoutView(timeout=1)
        components = self.regex_chuck_component(text)
        for component in components:
            view.add_item(self.component_process(component))
        return view

    def component_process(self, component: Union[str, dict]) -> Optional[Union[ui.Item, discord.MediaGalleryItem]]:
        data = component["data"] if isinstance(component, dict) else {}
        if isinstance(component, str):
            return ui.TextDisplay(content=component)
        elif component["type"] == "Container":
            container = ui.Container()
            for sub_item in component["component"]:
                container.add_item(self.component_process(sub_item))
            return container
        elif component["type"] == "SectionThumbnail":
            thumbnail = ui.Thumbnail(
                media=discord.UnfurledMediaItem(url=data["url"]),
                spoiler=bool(data.get("spoiler", False)),
                description=data["description"] if data["description"] else None
            )
            section = ui.Section(accessory=thumbnail)
            for sub_item in component["component"]:
                section.add_item(self.component_process(sub_item))
            return section
        elif component["type"] == "SectionButtonLink":
            button = ui.Button(label=data["label"], url=data["content"])
            section = ui.Section(accessory=button)
            for sub_item in component["component"]:
                section.add_item(self.component_process(sub_item))
            return section
        elif component["type"] == "SectionButton":
            button = ui.Button(
                label=data["label"],
                style=getattr(discord.ButtonStyle, data.get("style", "primary")),
                disabled=data.get("disabled", False)
            )
            section = ui.Section(accessory=button)
            for sub_item in component["component"]:
                section.add_item(self.component_process(sub_item))
            return section
        elif component["type"] == "MediaGallery":
            media_gallery = ui.MediaGallery(*[
                self.component_process(item) for item in component["component"]
            ])
            return media_gallery
        elif component["type"] == "ButtonLink":
            button = ui.Button(label=data["label"], url=data["url"])
            return button
        elif component["type"] == "Button":
            return ui.Button(
                label=data["label"],
                style=getattr(discord.ButtonStyle, data.get("style", "primary")),
                disabled=data.get("disabled", False)
            )
        elif component["type"] == "Select":
            options = [discord.SelectOption(label=opt, value=str(index)) for index, opt in enumerate(data["options"])]
            select = ui.Select(
                max_values=data["max"],
                min_values=data["min"],
                placeholder=data["placeholder"],
                options=options,
                disabled=data.get("disabled", False)
            )
            return ui.ActionRow(select)
        elif component["type"] == "ActionRow":
            action_row = ui.ActionRow()
            for item in component["component"]:
                action_row.add_item(self.component_process(item))
            return action_row
        elif component["type"] == "MediaGalleryItem":
            media_item = discord.MediaGalleryItem(
                    media=discord.UnfurledMediaItem(url=component["data"]["url"]),
                    spoiler=bool(component["data"].get("spoiler", False)),
                    description=component["data"]["description"] if component["data"]["description"] else None
                )
            return media_item
        elif component["type"] == "Separator":
            size = component["data"].get("size", 1)
            spacing = discord.SeparatorSpacing(size)
            return ui.Separator(spacing=spacing)


    async def format_user_message(self, message: discord.Message) -> list[dict]:
        context = {
            "User ID": message.author.id,
            "Username": message.author.name,
            "User Display Name": message.author.display_name,
            "Message ID": message.id
        }
        if isinstance(message.author, discord.Member):
            if message.author.nick:
                context["User Nickname"] = message.author.nick
        if message.reference:
            try:
                reply_message = await message.channel.fetch_message(message.reference.message_id)
                if reply_message.author.id == self.client.user.id:
                    context["Reply Your Message ID"] = reply_message.id
                    context["Reply To Your Message Content"] = await self.format_ai_message(reply_message)
                else:
                    context["Message Reply To Message ID"] = message.reference.message_id
                    context["Message Reply To Author"] = reply_message.author.name
                    context["Message Reply To Author ID"] = reply_message.author.id
                    context["Message Reply To Content"] = reply_message.content or "Empty Content"
            except discord.NotFound:
                pass
        context_string = "# User Message Context (Context for You)\n\n"
        context_string += '\n'.join([f'{k}: {v}' for k, v in context.items()])
        return [
            {"type": "text", "text": message.content},
            {"type": "text", "text": context_string}
        ]