import pytest
from backend.crud.users import create_user
from backend.crud.groups import create_group

@pytest.fixture()
def users(db):
    u1 = create_user(db, "alice", "alice@example.com", "hash1")
    u2 = create_user(db, "bob", "bob@example.com", "hash2")
    u3 = create_user(db, "cara", "cara@example.com", "hash3")
    return u1, u2, u3

@pytest.fixture()
def group(db, users):
    owner, bob, cara = users
    g = create_group(db, name="Trip", owner_id=owner.id, member_ids=[bob.id, cara.id], currency="GBP")
    return g
