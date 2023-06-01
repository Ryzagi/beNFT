import argparse
import asyncio
import logging
import re

import aiohttp
import base64
import discord

from io import BytesIO
from pathlib import Path

from discord.ext.commands import Bot
from discord import Message

intents = discord.Intents.default()
intents.members = True
bot = Bot(command_prefix='/', intents=intents)
MAX_MESSAGE_LENGTH = 2000
import os
#bot_token = os.environ.get('DISCORD_API_KEY')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--discord_token", help="Discord_token bot token", type=str, required=True
    )
    return parser.parse_args()


args = parse_args()


def try_(func):
    async def try_except(message):
        error = ""
        for i in range(4):
            try:
                await func(message)
                return None
            except Exception as e:
                print(e)
                error = str(e).lower()
                pass
            await asyncio.sleep(1)
        if "overloaded with other requests" in error:

            await message.channel.send("\nPlease, try again later, We are currently under heavy load")
        else:

            await message.channel.send('\nSomething went wrong, please type "/start" to start over')
        return None

    return try_except


@bot.command(name='start')
async def start(ctx):
    """
    This command will be called when user sends !start command
    """
    author_id = ctx.author.id
    await ctx.channel.typing()
    await asyncio.sleep(1)
    await ctx.channel.send("Hi there!\nI'm BeAI. How can I assist you today?")

# Define a handler for the "/refresh_data" command
@bot.command(name='refresh_data')
async def refresh_data(message: Message):
    # Show a "typing" action to the user
    await message.channel.typing()
    await message.channel.send("Please, wait while database is updating...")
    # Send a request to the FastAPI endpoint to refresh database
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/refresh_data",
                json={},
        ) as response:
            result_text = await response.json()
    # Show a "typing" action to the user
    await message.channel.typing()
    # Send results
    await message.channel.send(result_text['result'])

@bot.event
async def on_message(message: Message) -> None:
    if message.author == bot.user:
        return
    message.content = re.sub(r'<.*?>', '', message.content)

    if message.content.startswith('@BeAI'):
        message.content = message.content.replace('@BeAI', '')
    print(message.content)
    # DM only
    #if not isinstance(message.channel, discord.DMChannel):
    #    return

    if message.content.startswith('/start'):
        await start(message)
        return
    if message.content.startswith('/refresh_data'):
        await refresh_data(message)
        return
    await message.channel.typing()
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/message",
                json={"message": message.content},
        ) as response:
            chatbot_response = await response.json()
    await message.channel.typing()
    num_messages = len(chatbot_response["result"]) // MAX_MESSAGE_LENGTH
    await message.channel.typing()
    for i in range(num_messages + 1):
        await message.channel.typing()
        await asyncio.sleep(1)
        await message.channel.send(chatbot_response["result"][i * MAX_MESSAGE_LENGTH: (i + 1) * MAX_MESSAGE_LENGTH])


if __name__ == "__main__":
    #bot_token = args.discord_token
    bot.run(bot_token)
