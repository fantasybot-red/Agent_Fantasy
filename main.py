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

    messages = await client.get_messages_history(message)

    messages.insert(0, {
        "role": "system",
        "content": client.get_system_prompt(message)
    })

    async with message.channel.typing():
        full_response, message_response = await client.process_stream_response(
            messages,
            Context(message, client)
        )
    if full_response is None:
        return
    if message_response is None:
        await message.reply(full_response)
    else:
        await message_response.edit(content=full_response)



client.run(os.getenv('BOT_TOKEN'))
