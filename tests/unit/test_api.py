import datetime

import hashlib
import pytest

import src.otus_hw5.api as api
from tests.unit.redis_mock import get_store

class TestSuite():
    @pytest.fixture()
    def set_up(self,get_store):
        self.context = {}
        self.headers = {}
        self.store = get_store

    def get_response(self, request):
        return api.method_handler(
            {"body": request, "headers": self.headers},
            self.context,
            self.store,
        )

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            request["token"] = hashlib.sha512(
                (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode(
                    "utf-8"
                )
            ).hexdigest()
        else:
            msg = (
                request.get("account", "") + request.get("login", "") + api.SALT
            ).encode("utf-8")
            request["token"] = hashlib.sha512(msg).hexdigest()

    def test_empty_request(self,set_up):
        _, code = self.get_response({})
        assert code == api.INVALID_REQUEST

    @pytest.mark.parametrize("params",
        [
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
                "token": "sdd",
                "arguments": {},
            },
            {
                "account": "horns&hoofs",
                "login": "admin",
                "method": "online_score",
                "token": "",
                "arguments": {},
            },
        ]
    )
    def test_bad_auth(self,set_up, params):
        _, code = self.get_response(params)
        assert code == api.FORBIDDEN

    @pytest.mark.parametrize("params",
        [
            {
                "account": "horns&hoofs",
                "login": "h&f",
                "method": "online_score",
            },
            {"account": "horns&hoofs", "login": "h&f", "arguments": {}},
            {
                "account": "horns&hoofs",
                "method": "online_score",
                "arguments": {},
            },
        ]
    )
    def test_invalid_method_request(self,set_up, params):
        self.set_valid_auth(params)
        response, code = self.get_response(params)
        assert code == api.INVALID_REQUEST
        assert len(response) > 0

    @pytest.mark.parametrize("params",
        [
            {},
            {"phone": "79175002040"},
            {"phone": "89175002040", "email": "stupnikov@otus.ru"},
            {"phone": "79175002040", "email": "stupnikovotus.ru"},
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": -1,
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": "1",
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.1890",
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "XXX",
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": 1,
            },
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "s",
                "last_name": 2,
            },
            {
                "phone": "79175002040",
                "birthday": "01.01.2000",
                "first_name": "s",
            },
            {"email": "stupnikov@otus.ru", "gender": 1, "last_name": 2},
        ]
    )
    def test_invalid_score_request(self,set_up, params):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": params,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        assert code == api.INVALID_REQUEST
        assert len(response) > 0

    @pytest.mark.parametrize("params",
        [
            {"phone": "79175002040", "email": "stupnikov@otus.ru"},
            {"phone": 79175002040, "email": "stupnikov@otus.ru"},
            {
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "a",
                "last_name": "b",
            },
            {"gender": 0, "birthday": "01.01.2000"},
            {"gender": 2, "birthday": "01.01.2000"},
            {"first_name": "a", "last_name": "b"},
            {
                "phone": "79175002040",
                "email": "stupnikov@otus.ru",
                "gender": 1,
                "birthday": "01.01.2000",
                "first_name": "a",
                "last_name": "b",
            },
        ]
    )
    def test_ok_score_request(self,set_up, params):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "online_score",
            "arguments": params,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        assert code == api.OK
        score = response.get("score")
        assert isinstance(score, (int, float)) and score >= 0
        assert sorted(self.context["has"]) == sorted(params.keys())

    def test_ok_score_admin_request(self,set_up):
        arguments = {"phone": "79175002040", "email": "stupnikov@otus.ru"}
        request = {
            "account": "horns&hoofs",
            "login": "admin",
            "method": "online_score",
            "arguments": arguments,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        assert code == api.OK
        score = response.get("score")
        assert score == 42

    @pytest.mark.parametrize("params",
        [
            {},
            {"date": "20.07.2017"},
            {"client_ids": [], "date": "20.07.2017"},
            {"client_ids": {1: 2}, "date": "20.07.2017"},
            {"client_ids": ["1", "2"], "date": "20.07.2017"},
            {"client_ids": [1, 2], "date": "XXX"},
        ]
    )
    def test_invalid_interests_request(self,set_up, params):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": params,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        assert code == api.INVALID_REQUEST
        assert len(response) > 0

    @pytest.mark.parametrize("params",
        [
            {
                "client_ids": [1, 2, 3],
                "date": datetime.datetime.today().strftime("%d.%m.%Y"),
            },
            {"client_ids": [1, 2], "date": "19.07.2017"},
            {"client_ids": [0]},
        ]
    )
    def test_ok_interests_request(self,set_up, params):
        request = {
            "account": "horns&hoofs",
            "login": "h&f",
            "method": "clients_interests",
            "arguments": params,
        }
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        assert code == api.OK
        assert len(params["client_ids"]) == len(response)
        assert (
            all(
                v
                and isinstance(v, list)
                and all(isinstance(i, (bytes, str)) for i in v)
                for v in response.values()
            )
        )
        assert self.context.get("nclients") == len(params["client_ids"])


if __name__ == "__main__":
    pytest.main()
