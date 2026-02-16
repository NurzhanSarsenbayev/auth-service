from types import SimpleNamespace

import pytest

from db.postgres import get_session


class FakeSession:
    def __init__(self):
        self.rolled_back = False

    async def rollback(self):
        self.rolled_back = True


class FakeFactory:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        class Ctx:
            async def __aenter__(self_inner):
                return self._session

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return Ctx()


@pytest.mark.asyncio
async def test_get_session_rolls_back_on_exception():
    sess = FakeSession()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(session_factory=FakeFactory(sess))))

    gen = get_session(request)
    session = await gen.__anext__()
    assert session is sess

    with pytest.raises(RuntimeError):
        await gen.athrow(RuntimeError("boom"))

    assert sess.rolled_back is True
