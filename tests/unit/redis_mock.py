import datetime

import pytest

from src.otus_hw5.store import CACHE_DB, REMOTE_DB, ScoringStore


class RedisMock:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        val = self.cache.get(key, None)
        if val is None:
            return None
        elif val["period"] is None or val["period"] > datetime.datetime.now():
            return val["value"]
        else:
            del self.cache[key]
            return None

    def set(self, key, value):
        self.cache[key] = {"period": None, "value": str(value).encode("utf-8")}

    def expire(self, key, period):
        time_limit = datetime.datetime.now() + \
                     datetime.timedelta(seconds=period)
        if key in self.cache.keys():
            self.cache[key]["period"] = time_limit


@pytest.fixture()
def get_store():
    store = ScoringStore(".env")
    store.connections[CACHE_DB] = RedisMock()
    store.connections[REMOTE_DB] = RedisMock()
    yield store