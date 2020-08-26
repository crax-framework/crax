from crax.views import TemplateView


class LeagueAPlayersIndex(TemplateView):
    template = "leagueA_players_index.html"
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
            "player": params["player"],
            "optional": params["optional"],
        }


class LeagueAPlayersScores(TemplateView):
    template = "leagueA_players_scores.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        self.context = {"team_name": params["team_name"], "player": params["player"]}
