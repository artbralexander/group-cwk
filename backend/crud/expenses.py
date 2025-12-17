from typing import List
from sqlalchemy.orm import Session, selectinload
from backend.models.group import Expense, ExpenseSplit


def create_expense(
    db: Session,
    *,
    group_id: int,
    description: str,
    amount_cents: int,
    paid_by_id: int,
    splits: List[dict],
) -> Expense:
    expense = Expense(group_id=group_id, description=description, amount=amount_cents, paid_by_id=paid_by_id)
    db.add(expense)
    db.flush()

    for split in splits:
        db.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=split["user_id"],
                amount=split["amount_cents"],
            )
        )

    db.commit()
    db.refresh(expense)
    return expense


def list_expenses_for_group(db: Session, group_id: int) -> List[Expense]:
    return (
        db.query(Expense)
        .options(
            selectinload(Expense.paid_by),
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
        )
        .filter(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())
        .all()
    )


def get_expense(db: Session, expense_id: int) -> Expense | None:
    return (
        db.query(Expense)
        .options(
            selectinload(Expense.paid_by),
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
        )
        .filter(Expense.id == expense_id)
        .first()
    )


def update_expense(
    db: Session,
    expense: Expense,
    *,
    description: str,
    amount_cents: int,
    paid_by_id: int,
    splits: List[dict],
) -> Expense:
    expense.description = description
    expense.amount = amount_cents
    expense.paid_by_id = paid_by_id

    db.query(ExpenseSplit).filter(ExpenseSplit.expense_id == expense.id).delete()
    db.flush()

    for split in splits:
        db.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=split["user_id"],
                amount=split["amount_cents"],
            )
        )

    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense):
    db.query(ExpenseSplit).filter(ExpenseSplit.expense_id == expense.id).delete()
    db.delete(expense)
    db.commit()
