import os
import re
import time
import aiohttp
from classs import Module, tool, AIContext


class SearchHelper(Module):

    @tool(
        query="Search question",
    )
    async def search(self, ctx: AIContext, q: str):
        """
        Search for a query using search engine.
        This function get the search result from search engine.
        Use this to get real-time data like weather, news, time, etc.
        You should use Vietnamese query or English query to get the best result.
        You should say to user that result may not be accurate.
        Search query should be concise and clear.
        """
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
        list_result = []
        async with aiohttp.ClientSession() as session:
            async with session.get('https://coccoc.com/composer', params=params, headers=headers) as response:
                data = await response.json()
                for i in data["search"]["search_results"][:5]:
                    data = i
                    for k in data.keys():
                        if type(data[k]) != str:
                            continue
                        data[k] = re.sub(r'<.*?>', '', data[k])
                    if i["type"].startswith("ads"):
                        continue
                    elif i["type"] == "search":
                        data_temp = {"title": i["title"], "link": i["url"], "description": i["content"], "type": i["type"]}
                        data = data_temp
                    list_result.append(data)
        return list_result


async def setup(client):
    await client.add_module(SearchHelper(client))
