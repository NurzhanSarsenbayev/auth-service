from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from services.user import UserService


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class FakeSession:
    def __init__(self, execute_value=None):
        self.execute_value = execute_value
        self.added = []
        self.deleted = []
        self.committed = False
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def execute(self, _stmt):
        return FakeResult(self.execute_value)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed.append(obj)

    async def delete(self, obj):
        self.deleted.append(obj)


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_email():
    session = FakeSession()
    async def get_by_email(_email):
        return object()

    async def get_by_username(_u):
        return None

    repo = SimpleNamespace(
        session=session,
        get_by_email=get_by_email,
        get_by_username=get_by_username,
    )

    svc = UserService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.create_user("u", "e@example.com", "pwd")
    assert e.value.status_code == 400
    assert "Email already registered" in e.value.detail


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_username():
    session = FakeSession()
    async def get_by_email(_email):
        return None

    async def get_by_username(_u):
        return object()

    repo = SimpleNamespace(
        session=session,
        get_by_email=get_by_email,
        get_by_username=get_by_username,
    )
    svc = UserService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.create_user("u", "e@example.com", "pwd")
    assert e.value.status_code == 400
    assert "Username already taken" in e.value.detail


@pytest.mark.asyncio
async def test_update_user_rejects_when_no_changes():
    session = FakeSession(execute_value=None)
    repo = SimpleNamespace(session=session)
    svc = UserService(repo=repo, redis=None)

    current_user = SimpleNamespace(user_id="id1", username="old", hashed_password="h")
    update = SimpleNamespace(username=None, old_password=None, new_password=None)

    with pytest.raises(HTTPException) as e:
        await svc.update_user(current_user=current_user, update=update)
    assert e.value.status_code == 400
    assert "No changes provided" in e.value.detail


@pytest.mark.asyncio
async def test_update_user_rejects_username_taken():
    # execute returns a user -> means username already taken by someone else
    session = FakeSession(execute_value=object())
    repo = SimpleNamespace(session=session)
    svc = UserService(repo=repo, redis=None)

    current_user = SimpleNamespace(user_id="id1", username="old", hashed_password="h")
    update = SimpleNamespace(username="new", old_password=None, new_password=None)

    with pytest.raises(HTTPException) as e:
        await svc.update_user(current_user=current_user, update=update)
    assert e.value.status_code == 400
    assert "Username already taken" in e.value.detail


@pytest.mark.asyncio
async def test_delete_user_not_found():
    session = FakeSession()

    async def get_by_id(_uid):
        return None

    repo = SimpleNamespace(session=session, get_by_id=get_by_id)
    svc = UserService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.delete_user("missing")
    assert e.value.status_code == 404
    assert "User not found" in e.value.detail
