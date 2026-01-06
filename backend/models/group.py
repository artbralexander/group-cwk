from datetime import datetime, date
from typing import List, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, UniqueConstraint, DateTime, func, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.db import Base

if TYPE_CHECKING:
    from backend.models.user import User


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    currency: Mapped[str] = mapped_column(String(10), default="GBP")

    members: Mapped[List["GroupMember"]] = relationship(
        "GroupMember", back_populates="group", cascade="all, delete-orphan"
    )


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_members"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    group: Mapped["Group"] = relationship("Group", back_populates="members")
    # Avoid circular import by using string for target; SQLAlchemy resolves at runtime
    user: Mapped["User"] = relationship("User")

class GroupCategory(Base):
    __tablename__ = "group_categories"
    __table_args__ = (UniqueConstraint("group_id","name",name="uq_group_category_name"),)
    
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)

    name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(255))
    budget: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship("Group")
    splits: Mapped[List["CategorySplit"]] = relationship("CategorySplit",back_populates="category",cascade="all, delete-orphan")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="category")

class CategorySplit(Base):
    __tablename__ = "category_splits"
    __table_args__ = (UniqueConstraint("category_id","user_id",name="uq_category_split_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("group_categories.id"),index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    share: Mapped[int] = mapped_column(Integer)
    category: Mapped["GroupCategory"] = relationship("GroupCategory",back_populates="splits")
    user: Mapped["User"] = relationship("User")

class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("group_categories.id"), index=True, nullable=True)
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[int] = mapped_column(Integer)  # stored as cents
    paid_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship("Group")
    category: Mapped["GroupCategory"] = relationship("GroupCategory",back_populates="expenses")
    paid_by: Mapped["User"] = relationship("User")
    splits: Mapped[List["ExpenseSplit"]] = relationship(
        "ExpenseSplit", back_populates="expense", cascade="all, delete-orphan"
    )


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    __table_args__ = (UniqueConstraint("expense_id", "user_id", name="uq_expense_split_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column(Integer)  # stored as cents

    expense: Mapped["Expense"] = relationship("Expense", back_populates="splits")
    user: Mapped["User"] = relationship("User")


class GroupInvite(Base):
    __tablename__ = "group_invites"
    __table_args__ = (UniqueConstraint("group_id", "invitee_id", "status", name="uq_group_invite_pending"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    group: Mapped["Group"] = relationship("Group")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id])
    invitee: Mapped["User"] = relationship("User", foreign_keys=[invitee_id])


class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[int] = mapped_column(Integer)  # cents
    status: Mapped[str] = mapped_column(String(20), default="payer_confirmed")
    payer_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    receiver_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    group: Mapped["Group"] = relationship("Group")
    payer: Mapped["User"] = relationship("User", foreign_keys=[payer_id])
    receiver: Mapped["User"] = relationship("User", foreign_keys=[receiver_id])

class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("group_id", "name", name="uq_subscription_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)  # cents
    cadence: Mapped[str] = mapped_column(String(20))  # monthly|quarterly|yearly
    next_due_date: Mapped[date] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(String(255), default="")
    category_id: Mapped[int | None] = mapped_column(ForeignKey("group_categories.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    group: Mapped["Group"] = relationship("Group")
    category: Mapped["GroupCategory"] = relationship("GroupCategory")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    members: Mapped[List["SubscriptionMember"]] = relationship(
        "SubscriptionMember", back_populates="subscription", cascade="all, delete-orphan"
    )


class SubscriptionMember(Base):
    __tablename__ = "subscription_members"
    __table_args__ = (UniqueConstraint("subscription_id", "user_id", name="uq_subscription_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    share: Mapped[int] = mapped_column(Integer)  # weight, not percentage

    subscription: Mapped["Subscription"] = relationship("Subscription", back_populates="members")
    user: Mapped["User"] = relationship("User")
