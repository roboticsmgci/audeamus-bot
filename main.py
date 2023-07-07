import os

import discord
from dotenv import load_dotenv

from audeamus_bot.bot import FRCClient

load_dotenv()

GUILD_ID = os.getenv("GUILD_ID")
if GUILD_ID is None:
    raise NameError("GUILD_ID not found in .env file")
GUILD = discord.Object(GUILD_ID)

TEAM_NUMBER = int(os.getenv("TEAM_NUMBER"))

client = FRCClient(TEAM_NUMBER, GUILD)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if DISCORD_TOKEN is None:
    raise NameError("DISCORD_TOKEN not found in .env file")

client.run(DISCORD_TOKEN)
