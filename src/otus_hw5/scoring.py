import hashlib
import json
from datetime import datetime
from typing import Optional
import random

from src.otus_hw5.store import ScoringStore


def get_score(
    store: ScoringStore,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    birthday: Optional[datetime] = None,
    gender: Optional[int] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> float:
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        email or "",
        str(gender) if gender else "",
        birthday.strftime("%Y%m%d") if birthday else "",
    ]
    key = "uid:" + hashlib.md5("".join(key_parts).encode("utf-8")).hexdigest()

    # Try to get from cache
    score = store.cache_get(key)
    if score is not None:
        return float(score)

    # Calculate score
    score = 0.0
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender is not None:
        score += 1.5
    if first_name and last_name:
        score += 0.5

    # Cache the score for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store: ScoringStore, cid: int) -> list:
    key = f"i:{cid}"
    r = store.get(key)
    if r:
        return json.loads(r)
    interests = [
            "cars",
            "pets",
            "travel",
            "hi-tech",
            "sport",
            "music",
            "books",
            "tv",
            "cinema",
            "geek",
            "otus",
        ]
    sample = random.sample(interests, 2)
    store.set(key,json.dumps(sample),60 * 60)
    return sample
