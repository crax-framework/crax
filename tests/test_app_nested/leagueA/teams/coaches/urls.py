from crax.urls import Route, Url

from .controllers import (
    LeagueACoachesIndex,
    LeagueACoachesResults,
)

url_list = [
    Route(
        urls=(
            Url(
                r"/first_league_coaches/(?P<team_name>\w{0,30})/"
                r"(?P<coach>\w{0,30})/",
                name="first_league_coaches",
                type="re_path",
                namespace="leagueA.coaches",
            )
        ),
        handler=LeagueACoachesIndex,
    ),
    Route(
        urls=(
            Url(
                "/first_league_scores/<team_name>/<coach>/",
                name="first_league_coach_results",
                namespace="leagueA.coaches",
            )
        ),
        handler=LeagueACoachesResults,
    ),
]
