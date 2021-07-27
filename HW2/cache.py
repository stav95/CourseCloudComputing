class Cache:
    def __init__(self):
        self.cache = {}

    def put(self, key: str, data: object, expiration_date: str):
        self.cache[key] = {
            'data': data,
            'expiration_date': expiration_date
        }

    def get(self, key: str) -> object:
        return self.cache.get(key, {}).get('data', None)

    def get_all_cache(self) -> dict:
        return self.cache
