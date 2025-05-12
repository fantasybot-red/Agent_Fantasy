import io
import os

import aiohttp
import discord

from classs import Module, tool
from classs.AIContext import AIContext


class ImageGen(Module):

    @tool(
        prompt="Prompt for image generation",
        negative_prompt="Negative prompt for image generation",
        width="Width of the image max: 1920",
        height="Height of the image max: 1920",
    )
    async def generate_image(self, ctx: AIContext, prompt: str, negative_prompt: str,
                             width: int, height: int):
        """
        Generate an image from a given prompt.
        - You MUST call `set_status` before using this tool.
        - Prompt MUST be in English.
        - Prompt should be concise and clear.
        - Separate each key charter with a comma.
        - You not allow to generate image about NSFW content.
        - Recommend aspect ratio is 1:1, 16:9 or 9:16.
        - Width and height should be divisible by 16.
        - if you what to embed image file to message, you MUST follow the below format:
            ```
            attachment://{file_name}
            ```
        Example:
            ```
            attachment://image.png
            ```
        """

        token = os.getenv("HUGGINGFACE_TOKEN")
        modal = os.getenv("HUGGINGFACE_MODEL")
        if not token or not modal:
            return {
                "success": False,
                "reason": "Image generation is not enabled. Please contact the admin."
            }

        elif width > 1920 or height > 1920:
            return {
                "success": False,
                "reason": "Image size is too large. Max size is 1920x1072."
            }

        headers = {
            "Authorization": f"Bearer {token}",
        }

        data = {
            "inputs": prompt,
            "parameters": {
                "width": width,
                "height": height,
                "negative_prompt": negative_prompt,
            }
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(f"https://router.huggingface.co/hf-inference/models/{modal}",
                json=data,
                ) as r:
                if r.ok:
                    file_id = os.urandom(16).hex()
                    content = io.BytesIO(await r.read())
                    file = discord.File(content, filename=f"{file_id}.png")
                    await ctx.add_attachment(file)
                    return {
                        "success": True,
                        "reason": "Image generated successfully.",
                        "file_name": file.filename
                    }
                else:
                    data = await r.json()
                    return {
                        "success": False,
                        "reason": "Image generation failed.",
                        "error": data["error"]
                    }


async def setup(client):
    await client.add_module(ImageGen(client))
