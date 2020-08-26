from crax.views import TemplateView


class LeagueACoachesIndex(TemplateView):
    template = "leagueA_coaches_index.html"
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
            "coach": params["coach"],
        }


class LeagueACoachesResults(TemplateView):
    template = "leagueA_coaches_results.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        self.context = {"team_name": params["team_name"], "coach": params["coach"]}
