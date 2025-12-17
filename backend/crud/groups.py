from typing import Iterable, List
from sqlalchemy.orm import Session, selectinload
from backend.models.group import Group, GroupMember


def create_group(db: Session, *, name: str, owner_id: int, member_ids: Iterable[int], currency: str) -> Group:
    unique_member_ids = {owner_id}
    unique_member_ids.update(member_ids)

    group = Group(name=name, owner_id=owner_id, currency=currency)
    db.add(group)
    db.flush()

    for user_id in unique_member_ids:
        db.add(GroupMember(group_id=group.id, user_id=user_id))

    db.commit()
    db.refresh(group)
    return group


def get_groups_for_user(db: Session, user_id: int) -> List[Group]:
    return (
        db.query(Group)
        .join(GroupMember)
        .filter(GroupMember.user_id == user_id)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
        .all()
    )


def get_group_with_members(db: Session, group_id: int) -> Group | None:
    return (
        db.query(Group)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
        .filter(Group.id == group_id)
        .first()
    )


def is_user_in_group(db: Session, group_id: int, user_id: int) -> bool:
    return (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
        is not None
    )


def add_member_to_group(db: Session, group_id: int, user_id: int) -> GroupMember:
    existing = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    membership = GroupMember(group_id=group_id, user_id=user_id)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
