from typing import TypeVar, Generic

import aiohttp

T = TypeVar("T")

class BaseApi(Generic[T]):

    def __init__(self,
                 base_url: str):
        self.base_url = f"{base_url}"

    async def put(self, data=None) -> T:
        async with aiohttp.ClientSession() as session:
            async with session.put(url=self.base_url, json=data) as response:
                return await response.json()

    async def post_add(self, data=None) -> T:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=self.base_url, json=data) as response:
                return await response.json()

    async def post_one(self, data=None) -> T:
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}one/", json=data) as response:
                return await response.json()

    async def post_all(self, data=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url=f"{self.base_url}all/", json=data) as response:
                return await response.json()

    async def get_one_by_key_value(self, params=None) -> T:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}one/key_value/", params=params) as response:
                return await response.json()

    async def get_all_by_key_value(self, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}all/key_value/", params=params) as response:
                return await response.json()

    async def get_count_key_value(self, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=f"{self.base_url}count/key_value/", params=params) as response:
                return await response.json()

    async def delete(self, id: int) -> T:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url=f"{self.base_url}{id}/") as response:
                return await response.json()
