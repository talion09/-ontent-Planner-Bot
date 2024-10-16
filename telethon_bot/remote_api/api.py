import aiohttp


class Api:
    def __init__(self, base_url):
        self.base_url = base_url

    async def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}/"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                return await response.json()

    async def patch(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}/"
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, json=data) as response:
                return await response.json()

    async def put(self, endpoint = None, data=None):
        if endpoint:
            url = f"{self.base_url}/{endpoint}/"
        else:
            url = f"{self.base_url}/"
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=data) as response:
                return await response.json()

    async def delete(self, endpoint):
        url = f"{self.base_url}/{endpoint}/"
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                return await response.json()
