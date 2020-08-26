from crax.urls import Route, Url

from .views import (
    TeamLeagueAIndex,
    TeamLeagueAScores,
)

url_list = [
    Route(
        urls=(Url("/first_league/<team_name>/", name="first_league_teams")),
        handler=TeamLeagueAIndex,
    ),
    Route(urls=(Url("/first_league_scores/<team_name>/")), handler=TeamLeagueAScores),
]
