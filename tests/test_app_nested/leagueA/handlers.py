from crax.views import TemplateView


class LeagueAIndex(TemplateView):
    template = "leagueA_index.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        query = self.request.query
        self.context = {"query": query, "params": params}


class LeagueAScores(TemplateView):
    template = "leagueA_scores.html"
    methods = ["GET"]

    async def get(self):
        params = self.request.params
        query = self.request.query
        self.context = {"query": query, "params": params}
