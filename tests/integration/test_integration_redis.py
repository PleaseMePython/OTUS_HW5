import pytest

from time import sleep

from src.otus_hw5.store import ScoringStore

class TestRedis():
    @pytest.fixture()
    def real_store(self):
        return ScoringStore(".env")

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 60},
                              {"key": 3, "value": b"value2", "period": "red"},
                              {"key": "key3", "value": 16, "period": []}
                              ])
    def test_remote_db(self, real_store, params):
        real_store.set(key=params["key"],
                      value=params["value"],
                      period=params["period"])
        value = real_store.get(key=params["key"])
        if isinstance(params["value"],str):
            src_value = params["value"]
        elif isinstance(params["value"],bytes):
            src_value = params["value"].decode("utf-8")
        else:
            src_value = str(params["value"])
        assert value == src_value

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 2}
                              ])
    def test_remote_expire(self, real_store, params):
        real_store.set(key=params["key"],
                      value=params["value"],
                      period=params["period"])
        sleep(params["period"])
        value = real_store.get(key=params["key"])
        assert value is None

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1"}
                              ])
    def test_remote_db_none(self, real_store, params):
        value = real_store.get(key=params["key"])
        assert value is None

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 60},
                              {"key": 3, "value": b"value2", "period": "red"},
                              {"key": "key3", "value": 16, "period": []}
                              ])
    def test_cache_db(self, real_store, params):
        real_store.cache_set(key=params["key"],
                            value=params["value"],
                            period=params["period"])
        value = real_store.cache_get(key=params["key"])
        if isinstance(params["value"], str):
            src_value = params["value"]
        elif isinstance(params["value"], bytes):
            src_value = params["value"].decode("utf-8")
        else:
            src_value = str(params["value"])
        assert value == src_value

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1", "value": "value1", "period": 2}
                              ])
    def test_cache_expire(self, real_store, params):
        real_store.cache_set(key=params["key"],
                            value=params["value"],
                            period=params["period"])
        sleep(params["period"])
        value = real_store.cache_get(key=params["key"])
        assert value is None

    @pytest.mark.integration_test
    @pytest.mark.parametrize("params",
                             [{"key": "key1"}
                              ])
    def test_cache_db_none(self, real_store, params):
        value = real_store.cache_get(key=params["key"])
        assert value is None