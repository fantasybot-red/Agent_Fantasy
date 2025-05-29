import aiohttp
import discord.ui

from classs import Module, tool
from classs.AIContext import AIContext
from objs.ViewArgs import ViewArgs


class ModalSupport(Module):

    async def save_prompt(self, prompt: str):
        json_data = {
            "text": prompt,
            "ttl": "0"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post("https://bin.mudfish.net/api/text", json=json_data) as response:
                jdata_return = await response.json()
                return jdata_return["tid"]

    async def tranform_dict_to_view(self, view_dict: ViewArgs) -> discord.ui.View:
        view = discord.ui.View()
        for button in view_dict["buttons"]:
            custom_id = None
            if button.get("prompt"):
                custom_id = "prompt:" + await self.save_prompt(button["prompt"])
            if button.get("call_tool"):
                custom_id = "tool:" + button["call_tool"]
            button = discord.ui.Button(
                label=button["label"],
                style=discord.ButtonStyle[button["style"]],
                emoji=button.get("emoji"),
                custom_id=custom_id,
                url=button.get("link")
            )
            view.add_item(button)
        for select in view_dict["selects"]:
            custom_id = "prompt_select:" + await self.save_prompt(select["prompt"])
            options = [
                discord.SelectOption(
                    label=option["label"],
                    value=option["value"],
                    description=option.get("description"),
                ) for option in select["options"]
            ]
            select_menu = discord.ui.Select(
                placeholder=select.get("placeholder"),
                custom_id=custom_id,
                options=options,
                min_values=select.get("min_values", 1),
                max_values=select.get("max_values", 1)
            )
            view.add_item(select_menu)
        return view


    @tool()
    async def set_views(self, ctx: AIContext, view: ViewArgs):
        """
        Creates interactive buttons and select dropdowns for user input and choices or display links.
        **Usage:**
        - User decisions and option selection
        - Music player controls (play, pause, skip, etc.)
        - Always after search results to offer navigation choices
        - Link buttons (better than markdown links)
        - You should use link buttons for link like icon, avatar, etc.
        **Requirements:**
        - Clear, short text (no markdown/mentions)
        - Include `prompt` parameter for handling guidance
        - Maximum 10 elements per response
        - Single use only per conversation turn
        """
        if not view["selects"] and not view["buttons"]:
            return {"reason": "there are no buttons or selects to set", "success": False}
        elif len(view["selects"]) + len(view["buttons"]) > 10:
            return {"reason": "too many buttons or selects to set", "success": False}
        elif ctx.view:
            return {"reason": "view already set", "success": False}
        view = await self.tranform_dict_to_view(view)
        ctx.set_view(view)
        return {"success": True, "reason": "view set successfully"}


async def setup(client):
    await client.add_module(ModalSupport(client))
