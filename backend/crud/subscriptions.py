from datetime import date
from sqlalchemy.orm import Session, selectinload
from backend.models.group import Subscription, SubscriptionMember

def list_subscriptions_for_group(db: Session, group_id: int):
    return (
        db.query(Subscription)
        .options(selectinload(Subscription.members).selectinload(SubscriptionMember.user))
        .filter(Subscription.group_id == group_id)
        .order_by(Subscription.next_due_date.asc(), Subscription.id.asc())
        .all()
    )

def get_subscription(db: Session, sub_id: int):
    return (
        db.query(Subscription)
        .options(selectinload(Subscription.members).selectinload(SubscriptionMember.user))
        .filter(Subscription.id == sub_id)
        .first()
    )

def create_subscription(db: Session, *, group_id: int, name: str, amount_cents: int,
                        cadence: str, next_due: date, notes: str, category_id: int | None,
                        created_by_id: int, member_shares: list[dict]):
    sub = Subscription(
        group_id=group_id,
        name=name,
        amount=amount_cents,
        cadence=cadence,
        next_due_date=next_due,
        notes=notes or "",
        category_id=category_id,
        created_by_id=created_by_id,
    )
    db.add(sub)
    db.flush()
    for item in member_shares:
        db.add(SubscriptionMember(subscription_id=sub.id, user_id=item["user_id"], share=item["share"]))
    db.commit()
    db.refresh(sub)
    return sub

def update_subscription(db: Session, sub: Subscription, *, name: str, amount_cents: int,
                        cadence: str, next_due: date, notes: str, category_id: int | None,
                        member_shares: list[dict]):
    sub.name = name
    sub.amount = amount_cents
    sub.cadence = cadence
    sub.next_due_date = next_due
    sub.notes = notes or ""
    sub.category_id = category_id
    db.query(SubscriptionMember).filter(SubscriptionMember.subscription_id == sub.id).delete()
    for item in member_shares:
        db.add(SubscriptionMember(subscription_id=sub.id, user_id=item["user_id"], share=item["share"]))
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

def delete_subscription(db: Session, sub: Subscription):
    db.delete(sub)
    db.commit()
