import aiohttp
from classs import Module, tool
from classs.AIContext import AIContext


class ImageHelper(Module):

    async def fetch_waifu_pic(self, req_type: str, category: str) -> str:
        api_url = f"https://api.waifu.pics/{req_type}/{category}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                return data["url"]

    @tool()
    async def get_table_image(self, ctx: AIContext):
        """
        Get table image for send to discord.
        - No need to set status for this tool.
        """
        if not ctx.message.channel.nsfw:
            return {
                "success": False,
                "reason": "can not send this image In this channel"
            }

        url = await self.fetch_waifu_pic("nsfw", "waifu")
        return {
            "success": True,
            "reason": "Get table image successfully",
            "image_url": url
        }

    @tool()
    async def get_chair_image(self, ctx: AIContext):
        """
        Get chair image for send to discord.
        - No need to set status for this tool.
        """
        if not ctx.message.channel.nsfw:
            return {
                "success": False,
                "reason": "can not send this image In this channel"
            }

        url = await self.fetch_waifu_pic("nsfw", "neko")
        return {
            "success": True,
            "reason": "Get chair image successfully",
            "image_url": url
        }


async def setup(client):
    await client.add_module(ImageHelper(client))
