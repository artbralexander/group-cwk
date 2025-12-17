from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session, selectinload
from backend.models.group import Settlement


def list_settlements_for_group(db: Session, group_id: int) -> List[Settlement]:
    return (
        db.query(Settlement)
        .options(
            selectinload(Settlement.payer),
            selectinload(Settlement.receiver),
        )
        .filter(Settlement.group_id == group_id)
        .order_by(Settlement.created_at.desc())
        .all()
    )


def create_settlement_record(
    db: Session,
    *,
    group_id: int,
    payer_id: int,
    receiver_id: int,
    amount_cents: int,
) -> Settlement:
    settlement = Settlement(
        group_id=group_id,
        payer_id=payer_id,
        receiver_id=receiver_id,
        amount=amount_cents,
        status="payer_confirmed",
        payer_confirmed_at=datetime.now(timezone.utc),
    )
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


def get_settlement(db: Session, settlement_id: int) -> Settlement | None:
    return (
        db.query(Settlement)
        .options(
            selectinload(Settlement.payer),
            selectinload(Settlement.receiver),
        )
        .filter(Settlement.id == settlement_id)
        .first()
    )


def confirm_settlement(db: Session, settlement: Settlement) -> Settlement:
    settlement.status = "complete"
    settlement.receiver_confirmed_at = datetime.now(timezone.utc)
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement
