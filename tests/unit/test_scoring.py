from datetime import datetime
import random

from src.otus_hw5.scoring import get_interests, get_score
from src.otus_hw5.api import MALE
from tests.unit.redis_mock import get_store

import pytest

class TestScoring():
    @pytest.mark.parametrize("params",
                             [{"score":0.0},
                              {"phone": "79894528759",
                               "score": 1.5},
                              {"email": "somemail@mail.net",
                               "score": 1.5},
                              {"last_name": "Last",
                               "first_name": "First",
                               "score":0.5},
                              {"birthday": datetime.today(),
                               "gender": MALE,
                               "score": 1.5}
                              ])
    def test_get_score(self, get_store,params):
        score = get_score(store=get_store,
                          last_name=params.get("last_name",None),
                          first_name=params.get("first_name",None),
                          birthday=params.get("birthday",None),
                          gender=params.get("gender",None),
                          phone=params.get("phone",None),
                          email=params.get("email",None))

        assert score == params["score"]


    def test_get_interests(self, get_store):
        cid = random.randint(1,10)
        interests1 = get_interests(store=get_store,
                                   cid=cid)
        interests2 = get_interests(store=get_store,
                                   cid=cid)
        assert isinstance(interests1,list)
        assert isinstance(interests2, list)
        assert interests1 == interests2

if __name__ == "__main__":
    pytest.main()