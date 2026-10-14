"""Shared fixtures: a small synthetic dataset loaded into a FAKE MongoDB (mongomock)."""
import json

import mongomock
import pytest

from mongo.import_data import import_cases, import_events
from mongo.build_stats import build_stats
from mongo.synthetic.generate_events import write_files


@pytest.fixture(scope="session")
def synthetic_dir(tmp_path_factory):
    folder = tmp_path_factory.mktemp("synthetic")
    write_files(str(folder), n_cases=600, seed=7)
    return folder


@pytest.fixture(scope="session")
def truth(synthetic_dir):
    return {int(k): v for k, v in json.load(open(synthetic_dir / "ground_truth.json")).items()}


@pytest.fixture()
def db(synthetic_dir):
    database = mongomock.MongoClient()["test_db"]
    import_cases(database, synthetic_dir / "cases.jsonl")
    import_events(database, synthetic_dir / "citation_events.jsonl")
    return database


@pytest.fixture()
def db_with_stats(db):
    build_stats(db)
    return db
