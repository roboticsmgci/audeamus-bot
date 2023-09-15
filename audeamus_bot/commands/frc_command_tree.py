from discord import app_commands
import discord

from audeamus_bot.commands.frc_commands import FRCCommands


class FRCCommandTree(app_commands.CommandTree):
    def __init__(self, client: discord.Client, team_number: int, max_matches_per_page: int):
        super().__init__(client)
        self.add_command(FRCCommands(team_number, max_matches_per_page))

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed = discord.Embed(title="Command Error",
                              description="An error occurred. Make sure your parameters are correct.")
        await interaction.response.send_message(embed=embed)
        await super().on_error(interaction, error)
