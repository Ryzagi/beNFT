import argparse
import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import KeyboardButton
import numpy as np
import os
import aiohttp
import requests

MAX_MESSAGE_LENGTH = 4000
import os
#bot_token = os.environ.get('TELEGRAM_API_KEY')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--telegram_token", help="Telegram bot token", type=str, required=True
    )
    return parser.parse_args()


args = parse_args()
# Set up the Telegram bot
bot = Bot(token=bot_token)
dispatcher = Dispatcher(bot)

# Define a ReplyKeyboardMarkup to show a "start" button
RESTART_KEYBOARD = types.ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton('/start')]], resize_keyboard=True, one_time_keyboard=True
)


# Define a handler for the "/start" command
@dispatcher.message_handler(commands=["start"])
async def start(message: types.Message):
    # Show a "typing" action to the user
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)

    # Send a welcome message with a "start" button
    await bot.send_message(
        message.from_user.id,
        text="Hi there!\nI'm BeAI. How can I assist you today?",
        # reply_markup=RESTART_KEYBOARD
    )
    # Pause for 1 second
    await asyncio.sleep(1)


# Define a handler for the "/refresh_data" command
@dispatcher.message_handler(commands=["refresh_data"])
async def refresh_data(message: types.Message):
    # Show a "typing" action to the user
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
    await bot.send_message(
        message.from_user.id,
        text="Please, wait while database is updating..."
    )
    # Send a request to the FastAPI endpoint to refresh database
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/refresh_data",
                json={},
        ) as response:
            result_text = await response.json()
    # Show a "typing" action to the user
    await bot.send_chat_action(message.from_user.id, action=types.ChatActions.TYPING)
    # Send results
    await bot.send_message(
        message.from_user.id,
        text=result_text['result']
    )


# Define the handler function for the /query command
@dispatcher.message_handler()
async def handle_query_command(message: types.Message):
    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    # Send a request to the FastAPI endpoint to get the most relevant paragraph
    async with aiohttp.ClientSession() as session:
        # Example for MESSAGE_ENDPOINT
        async with session.post(
                "http://localhost:8000/api/message",
                json={"message": message.text},
        ) as response:
            result_text = await response.json()

    num_messages = len(result_text["result"]) // MAX_MESSAGE_LENGTH
    await bot.send_chat_action(
        message.from_user.id, action=types.ChatActions.TYPING
    )
    for i in range(num_messages + 1):
        await bot.send_chat_action(
            message.from_user.id, action=types.ChatActions.TYPING
        )
        await asyncio.sleep(1)
        await bot.send_message(
            message.from_user.id,
            text=result_text["result"][i * MAX_MESSAGE_LENGTH: (i + 1) * MAX_MESSAGE_LENGTH],
        )


# Start polling for updates from Telegram
if __name__ == "__main__":
    executor.start_polling(dispatcher, skip_updates=False)
