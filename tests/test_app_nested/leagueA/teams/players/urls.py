from crax.urls import Route, Url

from .controllers import (
    LeagueAPlayersIndex,
    LeagueAPlayersScores,
)

url_list = [
    Route(
        urls=(
            Url(
                r"/first_league/(?P<team_name>\w{0,30})/"
                r"(?P<player>\w{0,30})/(?:(?P<optional>\d+))?",
                name="first_league_players",
                type="re_path",
            )
        ),
        handler=LeagueAPlayersIndex,
    ),
    Route(
        urls=(
            Url(
                "/first_league_scores/<team_name>/<player>/",
                name="first_league_players_scores",
            )
        ),
        handler=LeagueAPlayersScores,
    ),
]
