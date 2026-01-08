from backend.crud.groups import create_group, get_groups_for_user, is_user_in_group, add_member_to_group

def test_create_group_adds_owner_and_members(db, users):
    owner, bob, cara = users
    g = create_group(db, name="G1", owner_id=owner.id, member_ids=[bob.id], currency="GBP")
    assert g.id is not None

    assert is_user_in_group(db, g.id, owner.id)
    assert is_user_in_group(db, g.id, bob.id)
    assert not is_user_in_group(db, g.id, cara.id)

def test_add_member_is_idempotent(db, group, users):
    _, bob, _ = users
    m1 = add_member_to_group(db, group.id, bob.id)
    m2 = add_member_to_group(db, group.id, bob.id)
    assert m1.id == m2.id  # doesn’t duplicate

def test_get_groups_for_user(db, group, users):
    owner, _, _ = users
    gs = get_groups_for_user(db, owner.id)
    assert any(g.id == group.id for g in gs)
