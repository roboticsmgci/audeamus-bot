from datetime import datetime, time
from math import ceil

import discord
from discord import app_commands

from audeamus_bot.helpers import format
from audeamus_bot.api import tba
from audeamus_bot.helpers.page import Page


class TBACommands(app_commands.Group):
    """Access FRC data through the TBA API."""
    
    def __init__(self, team_number: int, max_matches_per_page: int, *args, **kwargs):
        super().__init__(*args, **kwargs, name="tba")

        self.team_number = team_number
        self.max_matches_per_page = max_matches_per_page

    @app_commands.command(description="Gets the events played by a specific team this year.")
    @app_commands.describe(team_number="The team number")
    async def events(self, interaction: discord.Interaction, team_number: int = 0):
        if team_number == 0:
            team_number = self.team_number

        team_events_data = await tba.team_events_year(
            f"frc{team_number}", datetime.now().year)
        team_events = [f"""**{event["name"]} ({event["key"]})**
                                    *{event["start_date"]} - {event["end_date"]}{f' (Week {event["week"]})' if "week" in event else ""}*
                                    *{f'@ {event["location_name"]}' if "location_name" in event else ""}*"""
                       for event in team_events_data]
        description = "\n\n".join(team_events)

        embed = discord.Embed(title=f"Events - {team_number}", description=description)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Gets the predicted final rankings for a specific event.")
    @app_commands.describe(event_key="The event key")
    async def predictions(self, interaction: discord.Interaction, event_key: str):
        event_predictions_data = await tba.event_predictions(event_key)
        if event_predictions_data["ranking_predictions"] is None:
            await interaction.response.send_message("Predictions not available.")
            return

        rankings = sorted(event_predictions_data["ranking_predictions"],
                          key=lambda prediction: prediction[1][4], reverse=True)

        embed = discord.Embed(title=f"Predictions - {event_key}")
        for rank, team in enumerate(rankings, start=1):
            embed.add_field(name=f"{rank}. {team[0][3:]}", value=f"{round(team[1][4])} RP")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Gets the upcoming matches of a specific team.")
    @app_commands.describe(team_number="The team number")
    async def schedule(self, interaction: discord.Interaction, team_number: int = 0):
        if team_number == 0:
            team_number = self.team_number

        matches = await tba.team_matches_year_simple(
            f"frc{team_number}", datetime.now().year)
        next_matches = sorted(filter(lambda match: match["predicted_time"] is not None
                                                   and time.time() < match["predicted_time"],
                                     matches),
                              key=lambda event: event["predicted_time"])  # type: ignore

        if len(next_matches) == 0:
            await interaction.response.send_message(embed=discord.Embed(title="Upcoming Matches",
                                                                        description="No scheduled matches."))
            return

        current_event_key = next_matches[0]["event_key"]

        predictions = await tba.event_predictions(current_event_key)

        num_pages = ceil(len(next_matches) / self.max_matches_per_page)

        def formatter(page: int):
            page_matches = next_matches[page * self.max_matches_per_page:(page + 1) * self.max_matches_per_page]
            if (match_predictions := predictions["match_predictions"]) is not None:
                embed = format.format_matches(
                    page_matches, f"Upcoming Matches - {team_number} - Page {page + 1}/{num_pages}", team_number,
                    match_predictions)
            else:
                embed = format.format_matches(
                    page_matches, f"Upcoming Matches - {team_number} - Page {page + 1}/{num_pages}", team_number)
            return embed

        if num_pages > 1:
            view = Page(0, num_pages, formatter)
            await interaction.response.send_message(embed=formatter(0), view=view)
        else:
            await interaction.response.send_message(embed=formatter(0))

    @app_commands.command(description="Gets the past matches of a specific team.")
    @app_commands.describe(team_number="The team number")
    async def history(self, interaction: discord.Interaction, team_number: int = 0):

        if team_number == 0:
            team_number = self.team_number

        matches = await tba.team_matches_year_simple(
            f"frc{team_number}", datetime.now().year)
        previous_matches = sorted(filter(lambda match: match["predicted_time"] is not None
                                                       and match["predicted_time"] < time.time(),
                                         matches),
                                  key=lambda match: match["predicted_time"],  # type: ignore
                                  reverse=True)

        num_pages = ceil(len(previous_matches) / self.max_matches_per_page)

        def formatter(page: int):
            page_matches = previous_matches[page * self.max_matches_per_page:(page + 1) * self.max_matches_per_page]
            embed = format.format_matches(
                page_matches, f"Previous Matches - {team_number} - Page {page + 1}/{num_pages}", team_number)
            return embed

        if num_pages > 1:
            view = Page(0, num_pages, formatter)
            await interaction.response.send_message(embed=formatter(0), view=view)
        else:
            await interaction.response.send_message(embed=formatter(0))

    @app_commands.command(description="Gets the playoff bracket of a specific event.")
    @app_commands.describe(event_key="The event key")
    async def bracket(self, interaction: discord.Interaction, event_key: str):
        matches = await tba.event_matches_simple(event_key)
        playoff_matches = sorted(filter(lambda match: match["comp_level"] != "qm", matches),
                                 key=lambda match: match["set_number"])

        if len(playoff_matches) == 0:
            embed = discord.Embed(title="Playoff Bracket",
                                  description="No matches found.")
            await interaction.response.send_message(embed=embed)
            return

        if len(playoff_matches) >= 14:
            num_pages = 8
        elif len(playoff_matches) >= 13:
            num_pages = 7
        elif len(playoff_matches) >= 12:
            num_pages = 6
        elif len(playoff_matches) >= 11:
            num_pages = 5
        elif len(playoff_matches) >= 10:
            num_pages = 4
        elif len(playoff_matches) >= 8:
            num_pages = 3
        elif len(playoff_matches) >= 6:
            num_pages = 2
        else:
            num_pages = 1

        def formatter(page: int):
            if page == 0:
                return format.format_playoff_round(playoff_matches[:4],
                                                    f"Upper Round 1 - {event_key} - Page 1/{num_pages}")
            elif page == 1:
                return format.format_playoff_round(playoff_matches[4:6],
                                                    f"Lower Round 1 - {event_key} - Page 2/{num_pages}")
            elif page == 2:
                return format.format_playoff_round(playoff_matches[6:8],
                                                    f"Upper Round 2 - {event_key} - Page 3/{num_pages}")
            elif page == 3:
                return format.format_playoff_round(playoff_matches[8:10],
                                                    f"Lower Round 2 - {event_key} - Page 4/{num_pages}")
            elif page == 4:
                return format.format_playoff_round(playoff_matches[10:11],
                                                    f"Upper Finals - {event_key} - Page 5/{num_pages}")
            elif page == 5:
                return format.format_playoff_round(playoff_matches[11:12],
                                                    f"Lower Round 3 - {event_key} - Page 6/{num_pages}")
            elif page == 6:
                return format.format_playoff_round(playoff_matches[12:13],
                                                    f"Lower Finals - {event_key} - Page 7/{num_pages}")
            else:
                return format.format_playoff_round(playoff_matches[13:14],
                                                    f"Grand Finals - {event_key} - Page 8/{num_pages}")

        if num_pages > 1:
            view = Page(0, num_pages, formatter)
            await interaction.response.send_message(embed=formatter(0), view=view)
        else:
            await interaction.response.send_message(embed=formatter(0))