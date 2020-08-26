from crax.views import TemplateView


class TeamLeagueAIndex(TemplateView):
    template = "leagueA_teams_index.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        query = self.request.query
        query_team_name = None
        if query and "team_name" in query:
            query_team_name = query["team_name"]
        self.context = {
            "query_team_name": query_team_name,
            "params_team_name": params["team_name"],
        }


class TeamLeagueAScores(TemplateView):
    template = "leagueA_teams_scores.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        self.context = {"team_name": params["team_name"]}