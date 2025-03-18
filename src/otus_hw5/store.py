"""Key-value хранилище"""

import os

from pathlib import Path

from dotenv import dotenv_values

import functools

from typing import Dict

import redis
from redis.retry import Retry
from redis.exceptions import (TimeoutError, ConnectionError)
from redis.backoff import ExponentialBackoff

CACHE_DB: int = 0
REMOTE_DB: int = 1


def lazy_connect(db: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self,*args, **kwargs):
            if db not in self.connections.keys():
                self.connections[db] = self.setup_connection(db=db)
            res = func(self,*args, **kwargs)
            return res
        return wrapper
    return decorator


class ScoringStore:


    def __init__(self,envfile: str=".env"):
        self.config = {}
        dotenv_path = Path(__file__).parent.parent.parent.joinpath(envfile)
        if os.path.exists(dotenv_path):
            self.config = dotenv_values(dotenv_path)
        self.connections: Dict[int,redis.Redis] = {}

    def setup_connection(self,db:int) -> redis.Redis:
        connection = redis.Redis(
            host=self.config["REDIS_URL"],
            port=self.config["REDIS_PORT"],
            db=db,
            username=self.config["REDIS_USER"],
            password=self.config["REDIS_USER_PASSWORD"],
            retry=Retry(ExponentialBackoff(cap=10, base=1), retries=25),
            retry_on_error=[ConnectionError, TimeoutError, ConnectionResetError],
            health_check_interval=1,
        )
        return connection

    @lazy_connect(REMOTE_DB)
    def get(self, key, db=REMOTE_DB) -> str | None:
        binary = self.connections[db].get(key)
        return binary.decode("utf-8") if binary is not None else None

    @lazy_connect(REMOTE_DB)
    def set(self, key, value, period,db=REMOTE_DB) -> None:
        self.connections[db].set(key, value)
        if isinstance(period,int) and period > 0:
            self.connections[db].expire(key,period)

    @lazy_connect(CACHE_DB)
    def cache_get(self, key) -> str | None:
        try:
            value = self.get(key=key,db=CACHE_DB)
        except ConnectionError:
            value = None
        return value


    @lazy_connect(CACHE_DB)
    def cache_set(self, key, value, period) -> None:
        try:
            self.set(key, value, period,db=CACHE_DB)
        except ConnectionError:
            pass


