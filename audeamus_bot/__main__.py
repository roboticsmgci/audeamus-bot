import os

import discord
from dotenv import load_dotenv

from audeamus_bot import AudeamusBot

load_dotenv()

team_number = int(input("Enter your FRC team number: "))
guild_id = int(input("Enter your Discord guild ID: "))
guild = discord.Object(guild_id)

client = AudeamusBot(team_number, guild)

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if DISCORD_TOKEN is None:
    raise NameError("DISCORD_TOKEN environment variable not found")

if os.getenv("TBA_API_KEY") is None:
    raise NameError("TBA_API_KEY environment variable not found")

client.run(DISCORD_TOKEN)
