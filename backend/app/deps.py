"""Dependencies injected into route functions (tests swap get_db for a fake DB)."""
from common.settings import get_db as _get_db


def get_db():
    return _get_db()
