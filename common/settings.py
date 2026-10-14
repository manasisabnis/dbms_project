"""Shared settings. Reads values from environment variables / the .env file."""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "legal_citations")


@lru_cache(maxsize=1)
def _client():
    # Imported here so unit tests that never touch a real DB don't need a server.
    from pymongo import MongoClient

    return MongoClient(MONGO_URL)


def get_db():
    """Return the MongoDB database object (one shared client per process)."""
    return _client()[MONGO_DB]
