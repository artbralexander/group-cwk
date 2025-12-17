from typing import List
from sqlalchemy.orm import Session, selectinload
from backend.models.group import GroupInvite


def create_group_invite(db: Session, *, group_id: int, inviter_id: int, invitee_id: int) -> GroupInvite:
    invite = GroupInvite(
        group_id=group_id,
        inviter_id=inviter_id,
        invitee_id=invitee_id,
        status="pending",
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_pending_invite(db: Session, *, group_id: int, invitee_id: int) -> GroupInvite | None:
    return (
        db.query(GroupInvite)
        .filter(
            GroupInvite.group_id == group_id,
            GroupInvite.invitee_id == invitee_id,
            GroupInvite.status == "pending",
        )
        .first()
    )


def get_invite_by_id(db: Session, invite_id: int) -> GroupInvite | None:
    return (
        db.query(GroupInvite)
        .options(
            selectinload(GroupInvite.group),
            selectinload(GroupInvite.inviter),
            selectinload(GroupInvite.invitee),
        )
        .filter(GroupInvite.id == invite_id)
        .first()
    )


def list_pending_invites_for_user(db: Session, user_id: int) -> List[GroupInvite]:
    return (
        db.query(GroupInvite)
        .options(
            selectinload(GroupInvite.group),
            selectinload(GroupInvite.inviter),
            selectinload(GroupInvite.invitee),
        )
        .filter(GroupInvite.invitee_id == user_id, GroupInvite.status == "pending")
        .all()
    )


def accept_invite(db: Session, invite: GroupInvite):
    invite.status = "accepted"
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite
