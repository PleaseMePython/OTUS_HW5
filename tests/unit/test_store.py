"""Юнит-тесты ScoringStore"""

from time import sleep

import pytest

from tests.unit.redis_mock import get_store


class TestScoringStore:

    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 60},
                              {"key": 3, "value": b"value2", "period": "red"}
                              ])
    def test_remote_db(self, get_store, params):
        get_store.set(key=params["key"],
                      value=params["value"],
                      period=params["period"])
        value = get_store.get(key=params["key"])
        assert value == str(params["value"])

    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 2}
                              ])
    def test_remote_expire(self, get_store, params):
        get_store.set(key=params["key"],
                      value=params["value"],
                      period=params["period"])
        sleep(params["period"])
        value = get_store.get(key=params["key"])
        assert value is None

    @pytest.mark.parametrize("params",
                             [{"key": "key1"}
                              ])
    def test_remote_db_none(self, get_store, params):
        value = get_store.get(key=params["key"])
        assert value is None

    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 60},
                              {"key": 3, "value": b"value2", "period": "red"}
                              ])
    def test_cache_db(self, get_store, params):
        get_store.cache_set(key=params["key"],
                            value=params["value"],
                            period=params["period"])
        value = get_store.cache_get(key=params["key"])
        assert value == str(params["value"])

    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 2}
                              ])
    def test_cache_expire(self, get_store, params):
        get_store.cache_set(key=params["key"],
                            value=params["value"],
                            period=params["period"])
        sleep(params["period"])
        value = get_store.cache_get(key=params["key"])
        assert value is None

    @pytest.mark.parametrize("params",
                             [{"key": "key1"}
                              ])
    def test_cache_db_none(self, get_store, params):
        value = get_store.cache_get(key=params["key"])
        assert value is None


if __name__ == "__main__":
    pytest.main()
