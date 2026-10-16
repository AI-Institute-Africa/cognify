"""Shared test fixtures.

The existing test suite under backend/tests/ is mostly live-HTTP integration
tests (requests against a running, seeded deployment). The BRD CR 2026-10
payment/OTP engine also gets pure in-process tests here, using a minimal
in-memory fake of the small slice of the Motor (MongoDB async driver) API that
services/payment_status_service.py and services/otp_service.py actually call —
no real MongoDB needed to verify the calculation/eligibility/OTP logic.
"""
import copy
import pytest


class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, key, direction=1):
        reverse = direction < 0
        self._docs.sort(key=lambda d: d.get(key), reverse=reverse)
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=None):
        return copy.deepcopy(self._docs[:length] if length else self._docs)

    def __aiter__(self):
        self._iter = iter(copy.deepcopy(self._docs))
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


def _matches(doc, query):
    for key, expected in query.items():
        if key == "$or":
            if not any(_matches(doc, clause) for clause in expected):
                return False
            continue
        if key == "$and":
            if not all(_matches(doc, clause) for clause in expected):
                return False
            continue
        if isinstance(expected, dict) and set(expected.keys()) & {"$in", "$ne", "$gte", "$lte"}:
            if "$in" in expected and doc.get(key) not in expected["$in"]:
                return False
            if "$ne" in expected and doc.get(key) == expected["$ne"]:
                return False
            if "$gte" in expected and not (doc.get(key) is not None and doc.get(key) >= expected["$gte"]):
                return False
            if "$lte" in expected and not (doc.get(key) is not None and doc.get(key) <= expected["$lte"]):
                return False
        elif doc.get(key) != expected:
            return False
    return True


class _FakeCollection:
    def __init__(self):
        self.docs = []

    async def find_one(self, query=None, projection=None, sort=None):
        query = query or {}
        candidates = [d for d in self.docs if _matches(d, query)]
        if sort:
            key, direction = sort[0]
            candidates.sort(key=lambda d: d.get(key), reverse=(direction < 0))
        return copy.deepcopy(candidates[0]) if candidates else None

    def find(self, query=None, projection=None):
        query = query or {}
        return _FakeCursor([d for d in self.docs if _matches(d, query)])

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return doc

    async def update_one(self, query, update, upsert=False):
        candidates = [d for d in self.docs if _matches(d, query)]
        if not candidates:
            if upsert:
                new_doc = dict(query)
                self._apply(new_doc, update)
                self.docs.append(new_doc)
            return
        self._apply(candidates[0], update)

    async def count_documents(self, query=None):
        query = query or {}
        return len([d for d in self.docs if _matches(d, query)])

    @staticmethod
    def _apply(doc, update):
        if "$set" in update:
            doc.update(update["$set"])
        if "$inc" in update:
            for k, v in update["$inc"].items():
                doc[k] = doc.get(k, 0) + v
        if "$addToSet" in update:
            for k, v in update["$addToSet"].items():
                doc.setdefault(k, [])
                if v not in doc[k]:
                    doc[k].append(v)


class FakeDB:
    """Mimics `db.<collection_name>` attribute access against motor's AsyncIOMotorDatabase."""
    def __init__(self):
        self._collections = {}

    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = _FakeCollection()
        return self._collections[name]


@pytest.fixture
def fake_db():
    return FakeDB()
