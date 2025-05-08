from dotenv import load_dotenv

load_dotenv()

# Bot Core

import discord
import os

from classs import FClient, Context

client = FClient()


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if client.user not in message.mentions:
        return

    async with message.channel.typing():

        messages = await client.get_messages_history(message)

        messages.insert(0, {
            "role": "system",
            "content": client.get_system_prompt(message)
        })

        ctx, message_response = await client.process_stream_response(
            messages,
            Context(message, client)
        )
    await ctx.finish_response()



client.run(os.getenv('BOT_TOKEN'))
