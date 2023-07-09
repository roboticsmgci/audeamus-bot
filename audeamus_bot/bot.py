from audeamus_bot.commands.command_tree import TBACommandTree
from audeamus_bot.api import tba_api
import discord

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

MAX_MATCHES_PER_PAGE = 8


class AudeamusBot(discord.Client):
    def __init__(self, team_number: int, guild: discord.Object, **kwargs):
        super().__init__(intents=intents, **kwargs)

        self.team_number = team_number
        self.guild = guild
        self.tree = TBACommandTree(self, team_number, MAX_MATCHES_PER_PAGE)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

    async def on_ready(self):
        print(f"We have logged in as {self.user}")

    async def close(self):
        print("Closing")

        if tba_api.session is not None:
            await tba_api.session.close()
        await super().close()
