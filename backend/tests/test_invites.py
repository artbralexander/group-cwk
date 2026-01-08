from backend.crud.invites import create_group_invite, get_pending_invite, accept_invite, list_pending_invites_for_user

def test_invite_flow(db, group, users):
    owner, bob, _ = users

    inv = create_group_invite(db, group_id=group.id, inviter_id=owner.id, invitee_id=bob.id)
    assert inv.status == "pending"

    pending = get_pending_invite(db, group_id=group.id, invitee_id=bob.id)
    assert pending is not None

    lst = list_pending_invites_for_user(db, bob.id)
    assert len(lst) == 1

    accept_invite(db, inv)
    assert inv.status == "accepted"

    assert get_pending_invite(db, group_id=group.id, invitee_id=bob.id) is None
