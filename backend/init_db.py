from backend.db import engine
from backend.models.user import User
from backend.models.group import Group, GroupMember, GroupInvite, Expense, ExpenseSplit, Settlement

User.metadata.create_all(bind=engine)
Group.metadata.create_all(bind=engine)
GroupMember.metadata.create_all(bind=engine)
GroupInvite.metadata.create_all(bind=engine)
Expense.metadata.create_all(bind=engine)
ExpenseSplit.metadata.create_all(bind=engine)
Settlement.metadata.create_all(bind=engine)
