import os
import re
import time

import aiohttp
from classs import Module, tool, Context


class SearchHelper(Module):

    @tool(
        query="Search question",
    )
    async def search(self, ctx: Context, q: str):
        """
        Search for a query using search engine.
        This function get the search result from search engine.
        Use this to get real-time data like weather, news, time, etc.
        You should use Vietnamese query or English query to get the best result.
        Search query should be concise and clear.
        """
        special_data = await self.coccoc_search(q)
        web_data = await self.google_seach(q)
        return special_data + web_data

    async def coccoc_search(self, q: str):
        headers = {
            'referer': 'https://coccoc.com/search',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Cookie': 'serp_version=29096805/6890410',
        }

        params = {
            '_': str(int(time.time() * 1000)),
            'p': '0',
            'q': q,
            'reqid': os.urandom(4).hex(),
            'apiV': '1',
        }
        special_data = []
        async with aiohttp.ClientSession() as session:
            async with session.get('https://coccoc.com/composer', params=params, headers=headers) as response:
                data = await response.json()
                for i in data["search"]["search_results"]:
                    data = i
                    for k in data.keys():
                        if type(data[k]) != str:
                            continue
                        data[k] = re.sub(r'<.*?>', '', data[k])
                    if i["type"].startswith("ads"):
                        continue
                    elif i["type"] == "search":
                        continue
                    special_data.append(data)
        return special_data

    async def google_seach(self, q: str):
        if os.getenv("GOOGLE_API_KEY") is None or os.getenv("GOOGLE_CX_ID") is None:
            return []
        payload = {
            "key": os.getenv("GOOGLE_API_KEY"),
            "cx": os.getenv("GOOGLE_CX_ID"),
            "q": q,
            "num": 10
        }
        async with aiohttp.ClientSession() as s:
            async with s.get("https://www.googleapis.com/customsearch/v1", params=payload) as r:
                djson = await r.json()
        search_results = []
        for item in djson.get("items", []):
            search_results.append({
                "url": item['link'],
                "title": item['title'],
                "description": item.get('snippet', ""),
                "type": "web",
            })
        return search_results

async def setup(client):
    await client.add_module(SearchHelper(client))
