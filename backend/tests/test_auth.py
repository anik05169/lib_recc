import pytest
from bson import ObjectId

from app.core.auth import get_user_by_id


class FakeCollection:
    def __init__(self, doc):
        self.doc = doc

    def find_one(self, query):
        if query.get("_id") == self.doc["_id"]:
            return self.doc
        return None


class FakeDb:
    def __init__(self, user):
        self.users = FakeCollection(user)


def test_get_user_by_id_invalid_returns_none(monkeypatch):
    user = {"_id": ObjectId(), "email": "a@b.com"}

    def fake_get_db():
        return FakeDb(user)

    monkeypatch.setattr("app.core.auth.get_mongo_db", fake_get_db)
    assert get_user_by_id("not-a-valid-object-id") is None


def test_get_user_by_id_valid(monkeypatch):
    oid = ObjectId()
    user = {"_id": oid, "email": "a@b.com"}

    def fake_get_db():
        return FakeDb(user)

    monkeypatch.setattr("app.core.auth.get_mongo_db", fake_get_db)
    assert get_user_by_id(str(oid)) == user
