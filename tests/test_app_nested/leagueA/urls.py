from crax.urls import Route, Url, include

from .handlers import (
    LeagueAIndex,
    LeagueAScores,
)

url_list = [
    Route(urls=(Url("/first_league/", name="first_league")), handler=LeagueAIndex),
    Route(
        urls=(Url("/first_league_scores", name="first_league_scores")),
        handler=LeagueAScores,
    ),
]
