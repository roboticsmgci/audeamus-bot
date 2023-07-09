from datetime import datetime
from typing import Optional

import discord

from audeamus_bot.api import tba_api
from audeamus_bot.types.tba_types import MatchPredictions, MatchSimple


def format_matches(matches: list[MatchSimple], title: str, team_number: int = 0,
                   predictions: Optional[MatchPredictions] = None) -> discord.Embed:
    embed = discord.Embed(title=title)
    last_event_key = ""

    for match in matches:
        if match["event_key"] != last_event_key:
            embed.add_field(name=f"__**{match['event_key']}**__", value="")
            last_event_key = match['event_key']

        if match["predicted_time"] is None:
            time_text = ""
        else:
            time_text = datetime.fromtimestamp(
                match["predicted_time"]).strftime("%a %I:%M %p")

        if match["alliances"] is None:
            alliances_text = ""
        else:
            red_alliance = [(team_key[3:] if str(team_number) != team_key[3:]
                             else f"__{team_key[3:]}__")
                            for team_key in match["alliances"]["red"]["team_keys"]]
            blue_alliance = [(team_key[3:] if str(team_number) != team_key[3:]
                              else f"__{team_key[3:]}__")
                             for team_key in match["alliances"]["blue"]["team_keys"]]

            # If the match score has been updated
            if match["alliances"]["red"]["score"] != -1:
                red_points = match["alliances"]["red"]["score"]
                blue_points = match["alliances"]["blue"]["score"]
                red_alliance_text = f"{'-'.join(red_alliance)} ({red_points})"
                blue_alliance_text = f"({blue_points}) {'-'.join(blue_alliance)}"
                if match["winning_alliance"] == "red":
                    red_alliance_text = f"**{red_alliance_text}**"
                elif match["winning_alliance"] == "blue":
                    blue_alliance_text = f"**{blue_alliance_text}**"
            elif predictions is not None:  # If predictions are available
                if match["comp_level"] == "qm":
                    prediction = predictions["qual"][match["key"]]
                else:
                    prediction = predictions["playoff"][match["key"]]

                red_points = round(prediction["red"]["score"])
                blue_points = round(prediction["blue"]["score"])

                red_alliance_text = f"{'-'.join(red_alliance)} ({red_points}\\*)"
                blue_alliance_text = f"({blue_points}\\*) {'-'.join(blue_alliance)}"

                if prediction["winning_alliance"] == "red":
                    red_alliance_text = f"*{red_alliance_text}*"
                elif prediction["winning_alliance"] == "blue":
                    blue_alliance_text = f"*{blue_alliance_text}*"

                embed.set_footer(text="* Predicted Points")
            else:
                red_alliance_text = "-".join(red_alliance)
                blue_alliance_text = "-".join(blue_alliance)

            alliances_text = f"{red_alliance_text} vs {blue_alliance_text}"

        if match["comp_level"] == "qm":
            match_name = f"Qualification {match['match_number']}"
        elif match["comp_level"] == "sf":
            if match["set_number"] in [1, 2, 3, 4]:
                match_name = f"Upper Quarterfinals"
            elif match["set_number"] in [5, 6]:
                match_name = f"Lower Round 1"
            elif match["set_number"] in [7, 8]:
                match_name = f"Upper Semifinals"
            elif match["set_number"] in [9, 10]:
                match_name = f"Lower Round 2"
            elif match["set_number"] == 11:
                match_name = f"Upper Finals"
            elif match["set_number"] == 12:
                match_name = f"Lower Round 3"
            elif match["set_number"] == 13:
                match_name = f"Lower Finals"
            elif match["set_number"] == 14:
                match_name = f"Finals"
            else:
                match_name = f"Playoff Match"

            match_name += f" ({match['set_number']})"

        elif match["comp_level"] == "f":
            match_name = f"Finals {match['match_number']}"
        else:
            match_name = "Match"

        embed.add_field(name=f"{match_name} | {time_text}",
                        value=alliances_text, inline=False)

    return embed


def format_playoff_round(matches: list[MatchSimple], title: str) -> discord.Embed:
    match_descriptions = []
    for match in matches:
        if match["alliances"] is not None:
            match_description = "__"
            red_alliance = "-".join(key[3:] for key in match["alliances"]["red"]["team_keys"])
            red_alliance_space = 15 - len(red_alliance)
            blue_alliance = "-".join(key[3:] for key in match["alliances"]["blue"]["team_keys"])
            blue_alliance_space = 15 - len(blue_alliance)

            match_description += "`" + (" " * red_alliance_space) + red_alliance + "`"
            match_description += "\\_" * 3
            match_description += "__\n__"
            match_description += "`" + (" " * blue_alliance_space) + blue_alliance + "`"
            match_description += "\\_" * 3
            match_description += "__" + ("\N{Overline}" * 5)

            match_descriptions.append(match_description)

    embed = discord.Embed(title=title, description="\n\n".join(match_descriptions))
    return embed


async def get_current_event(team_number: int):
    events = await tba_api.team_events_year(f"frc{team_number}", 2023)
    for event in events:
        current_date = datetime.now()
        start_date = datetime.strptime(event["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(event["end_date"], "%Y-%m-%d")
        if start_date < current_date < end_date:
            return event["event_code"]
    return None
