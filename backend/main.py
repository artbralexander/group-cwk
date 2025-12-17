import os
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Iterable
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadTimeSignature
from fastapi import FastAPI, Depends, HTTPException, Response, Request, status, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db import get_db, SessionLocal, Base, engine
from backend.crud.users import get_user_by_username, create_user, get_user_by_email, update_user
from backend.crud.groups import (
    create_group as persist_group,
    get_groups_for_user,
    get_group_with_members,
    is_user_in_group,
)
from backend.crud.invites import (
    create_group_invite,
    get_pending_invite,
    list_pending_invites_for_user,
    get_invite_by_id,
)
from backend.crud.expenses import (
    create_expense,
    list_expenses_for_group,
    get_expense,
    update_expense,
    delete_expense,
)
from backend.crud.settlements import (
    create_settlement_record,
    list_settlements_for_group,
    get_settlement,
    confirm_settlement,
)
from backend.models.group import Group, GroupInvite, GroupMember, Expense, Settlement
app = FastAPI()

FRONTEND_DIST = os.getenv(
    "FRONTEND_DIST",
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
FRONTEND_INDEX = os.path.join(FRONTEND_DIST, "index.html")

if os.path.isdir(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")


def ensure_database():
    from backend.models import user, group  # noqa: F401
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    ensure_database()


#Models

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None = None


class GroupMemberResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    role: str = "member"


class GroupResponse(BaseModel):
    id: int
    name: str
    members: List[GroupMemberResponse]
    currency: str
    owner_id: int


class GroupCreateRequest(BaseModel):
    name: str
    members: List[str] = []
    currency: str | None = None


class GroupUpdateRequest(BaseModel):
    name: str | None = None
    currency: str | None = None


class InviteCreateRequest(BaseModel):
    username: str


class InviteResponse(BaseModel):
    id: int
    group_id: int
    group_name: str
    inviter_username: str
    status: str


class UpdateProfileRequest(BaseModel):
    email: EmailStr | None = None
    current_password: str | None = None
    new_password: str | None = None


class ExpenseSplitInput(BaseModel):
    username: str
    amount: float


class ExpenseCreateRequest(BaseModel):
    description: str
    amount: float
    paid_by: str
    splits: List[ExpenseSplitInput]
    split_members: List[str] | None = None


class ExpenseSplitResponse(BaseModel):
    username: str
    amount: float


class ExpenseResponse(BaseModel):
    id: int
    description: str
    amount: float
    paid_by: str
    created_at: str
    splits: List[ExpenseSplitResponse]


class SettlementResponse(BaseModel):
    payer: str
    receiver: str
    amount: float


class SettlementRecordResponse(BaseModel):
    id: int
    payer: str
    receiver: str
    amount: float
    status: str
    payer_confirmed: bool
    receiver_confirmed: bool
    created_at: str


class SettlementSummaryResponse(BaseModel):
    recommendations: List[SettlementResponse]
    records: List[SettlementRecordResponse]


class SettlementRecordRequest(BaseModel):
    receiver: str
    amount: float


SETTLEMENT_APPLIED_STATUSES = {"payer_confirmed", "complete"}
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
SESSION_SALT = "session-cookie"
serializer = URLSafeTimedSerializer(SECRET_KEY, salt=SESSION_SALT)


def dollars_to_cents(value) -> int:
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def cents_to_dollars(value: int) -> float:
    return float(Decimal(value) / Decimal(100))


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        websockets = self.connections.get(user_id)
        if not websockets:
            return
        websockets.discard(websocket)
        if not websockets:
            self.connections.pop(user_id, None)

    async def send(self, user_id: int, message: dict):
        websockets = list(self.connections.get(user_id, []))
        for socket in websockets:
            try:
                await socket.send_json(message)
            except RuntimeError:
                self.disconnect(user_id, socket)


manager = ConnectionManager()


def notify_users(background_tasks: BackgroundTasks | None, user_ids: Iterable[int], message: dict):
    if background_tasks is None:
        return
    unique_ids = {user_id for user_id in user_ids if user_id}
    for user_id in unique_ids:
        background_tasks.add_task(manager.send, user_id, message)


def notify_settlement_update(
    background_tasks: BackgroundTasks | None, group_id: int, user_ids: Iterable[int]
):
    notify_users(
        background_tasks,
        user_ids,
        {"type": "settlement_update", "data": {"group_id": group_id}},
    )


def notify_group_members(
    background_tasks: BackgroundTasks | None,
    group: Group | None,
    message: dict,
    exclude_user_ids: Iterable[int] | None = None,
):
    if background_tasks is None or not group:
        return
    excluded = set(exclude_user_ids or [])
    member_ids = [
        member.user_id
        for member in getattr(group, "members", [])
        if member.user_id and member.user_id not in excluded
    ]
    if member_ids:
        notify_users(background_tasks, member_ids, message)
def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        return False


def authenticate_user(username: str, password: str, db: Session):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_session(username: str) -> str:
    return serializer.dumps({"sub": username})


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_session_username(session_token: str) -> str | None:
    if not session_token:
        return None
    try:
        data = serializer.loads(session_token)
    except (BadSignature, BadTimeSignature):
        return None
    return data.get("sub")


def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    username = get_session_username(session_token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return user


def serialize_group(group: Group) -> GroupResponse:
    member_payloads = []
    for membership in group.members:
        if membership.user:
            member_payloads.append(
                GroupMemberResponse(
                    id=membership.user.id,
                    username=membership.user.username,
                    email=membership.user.email,
                    role="owner" if membership.user_id == group.owner_id else "member",
                )
            )
    return GroupResponse(
        id=group.id,
        name=group.name,
        members=member_payloads,
        currency=group.currency,
        owner_id=group.owner_id,
    )


def serialize_invite(invite: GroupInvite) -> InviteResponse:
    return InviteResponse(
        id=invite.id,
        group_id=invite.group_id,
        group_name=invite.group.name if invite.group else "",
        inviter_username=invite.inviter.username if invite.inviter else "",
        status=invite.status,
    )


def serialize_expense(expense: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=expense.id,
        description=expense.description,
        amount=cents_to_dollars(expense.amount),
        paid_by=expense.paid_by.username if expense.paid_by else "",
        created_at=expense.created_at.isoformat(),
        splits=[
            ExpenseSplitResponse(
                username=split.user.username if split.user else "",
                amount=cents_to_dollars(split.amount),
            )
            for split in expense.splits
        ],
    )


def calculate_member_balances(
    group,
    expenses: List[Expense],
    completed_settlements: List[Settlement] | None = None,
) -> dict[int, int]:
    member_ids = [member.user_id for member in group.members if member.user]
    balances = {user_id: 0 for user_id in member_ids}

    for expense in expenses:
        if expense.paid_by_id in balances:
            balances[expense.paid_by_id] += expense.amount
        for split in expense.splits:
            if split.user_id in balances:
                balances[split.user_id] -= split.amount

    if completed_settlements:
        for record in completed_settlements:
            if record.payer_id in balances:
                balances[record.payer_id] += record.amount
            if record.receiver_id in balances:
                balances[record.receiver_id] -= record.amount

    return balances


def calculate_settlements(
    group,
    expenses: List[Expense],
    completed_settlements: List[Settlement] | None = None,
) -> List[SettlementResponse]:
    members = {member.user_id: member.user for member in group.members if member.user}
    balances = calculate_member_balances(group, expenses, completed_settlements)

    creditors = []
    debtors = []
    for user_id, balance in balances.items():
        if balance > 0:
            creditors.append([user_id, balance])
        elif balance < 0:
            debtors.append([user_id, -balance])

    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)

    settlements: List[SettlementResponse] = []
    i = j = 0
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt_amount = debtors[i]
        creditor_id, credit_amount = creditors[j]
        payment = min(debt_amount, credit_amount)
        settlements.append(
            SettlementResponse(
                payer=members[debtor_id].username,
                receiver=members[creditor_id].username,
                amount=cents_to_dollars(payment),
            )
        )
        debtors[i][1] -= payment
        creditors[j][1] -= payment
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    return settlements


def serialize_settlement_record(record: Settlement) -> SettlementRecordResponse:
    return SettlementRecordResponse(
        id=record.id,
        payer=record.payer.username if record.payer else "",
        receiver=record.receiver.username if record.receiver else "",
        amount=cents_to_dollars(record.amount),
        status=record.status,
        payer_confirmed=record.payer_confirmed_at is not None,
        receiver_confirmed=record.receiver_confirmed_at is not None,
        created_at=record.created_at.isoformat(),
    )


@app.get("/api/health")
def health():
    return {"ok": True}



@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(data.username, data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # set cookie here on success
    response.set_cookie(
        key="session",
        value=create_session(user.username),
        httponly=True,
        samesite="lax",
    )

    return {"result": True}


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    if len(password) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at most 64 characters long",
        )


@app.post("/api/auth/register")
def register(data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    existing_email = get_user_by_email(db, data.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if data.password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    validate_password(data.password)

    user = create_user(db, data.username, data.email, hash_password(data.password))
    response.set_cookie(
        key="session",
        value=create_session(user.username),
        httponly=True,
        samesite="lax",
    )
    return {"id": user.id, "username": user.username}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"result": True}


@app.get("/api/auth/me", response_model=UserResponse)
def auth_me(current_user=Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email)


@app.put("/api/auth/me", response_model=UserResponse)
def update_profile(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = payload.email
    new_password = payload.new_password
    current_password = payload.current_password

    if email and email != current_user.email:
        if get_user_by_email(db, email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    password_hash = None
    if new_password:
        if not current_password or not verify_password(current_password, current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        validate_password(new_password)
        password_hash = hash_password(new_password)

    updated_user = update_user(
        db,
        current_user,
        email=email if email is not None else None,
        password_hash=password_hash,
    )

    return UserResponse(id=updated_user.id, username=updated_user.username, email=updated_user.email)


@app.get("/api/groups", response_model=List[GroupResponse])
def list_groups(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    groups = get_groups_for_user(db, current_user.id)
    return [serialize_group(group) for group in groups]


@app.post("/api/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group_endpoint(
    payload: GroupCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name is required")

    member_usernames = {username.strip() for username in payload.members if username.strip()}
    member_usernames.discard(current_user.username)

    member_ids: List[int] = []
    for username in member_usernames:
        member = get_user_by_username(db, username)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User '{username}' not found",
            )
        member_ids.append(member.id)

    currency = (payload.currency or "GBP").upper()
    group = persist_group(db, name=name, owner_id=current_user.id, member_ids=member_ids, currency=currency)
    group_with_members = get_group_with_members(db, group.id) or group
    return serialize_group(group_with_members)


@app.put("/api/groups/{group_id}", response_model=GroupResponse)
def update_group_endpoint(
    group_id: int,
    payload: GroupUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can update the group")

    updated = False
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Group name is required")
        group.name = name
        updated = True
    if payload.currency is not None:
        currency = payload.currency.strip().upper()
        if not currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Currency is required")
        group.currency = currency
        updated = True

    if updated:
        db.add(group)
        db.commit()
        db.refresh(group)

    group_payload = serialize_group(group)
    if updated:
        notify_group_members(
            background_tasks,
            group,
            {"type": "group_updated", "data": group_payload.dict()},
            exclude_user_ids=[current_user.id],
        )
    return group_payload


@app.get("/api/groups/{group_id}", response_model=GroupResponse)
def get_group_endpoint(
    group_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_ids = {member.user_id for member in group.members}
    if current_user.id not in member_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return serialize_group(group)


@app.post("/api/groups/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_group(
    group_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    membership = next((member for member in group.members if member.user_id == current_user.id), None)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group")
    if group.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group owners must delete the group instead of leaving",
        )

    expenses = list_expenses_for_group(db, group_id)
    records = list_settlements_for_group(db, group_id)
    applied_records = [record for record in records if record.status in SETTLEMENT_APPLIED_STATUSES]
    balances = calculate_member_balances(group, expenses, applied_records)
    if balances.get(current_user.id, 0) != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settle all outstanding balances before leaving the group",
        )

    db.delete(membership)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.delete("/api/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_endpoint(
    group_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if group.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the owner can delete this group")

    expenses = list_expenses_for_group(db, group_id)
    records = list_settlements_for_group(db, group_id)
    applied_records = [record for record in records if record.status in SETTLEMENT_APPLIED_STATUSES]
    balances = calculate_member_balances(group, expenses, applied_records)
    if any(amount != 0 for amount in balances.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settle all outstanding balances before deleting the group",
        )

    for record in records:
        db.delete(record)
    for expense in expenses:
        db.delete(expense)
    invites = db.query(GroupInvite).filter(GroupInvite.group_id == group_id).all()
    for invite in invites:
        db.delete(invite)

    db.delete(group)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def validate_expense_payload(group, payload: ExpenseCreateRequest):
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")
    member_map = {member.user.username: member.user for member in group.members if member.user}
    if payload.paid_by not in member_map:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payer must be in group")
    if not payload.splits:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Splits are required")

    amount_cents = dollars_to_cents(payload.amount)
    total_split = 0
    split_items = []
    for split in payload.splits:
        user = member_map.get(split.username)
        if not user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User {split.username} not in group")
        if split.amount < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Split amount must be positive")
        split_cents = dollars_to_cents(split.amount)
        total_split += split_cents
        split_items.append({"user_id": user.id, "amount_cents": split_cents})
    if total_split != amount_cents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Splits must sum to total amount")
    return member_map[payload.paid_by], split_items, amount_cents


@app.get("/api/groups/{group_id}/expenses", response_model=List[ExpenseResponse])
def get_group_expenses(
    group_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    expenses = list_expenses_for_group(db, group_id)
    return [serialize_expense(exp) for exp in expenses]


@app.post("/api/groups/{group_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_group_expense(
    group_id: int,
    payload: ExpenseCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    payer, split_items, amount_cents = validate_expense_payload(group, payload)
    expense = create_expense(
        db,
        group_id=group_id,
        description=payload.description.strip(),
        amount_cents=amount_cents,
        paid_by_id=payer.id,
        splits=split_items,
    )
    expenses = list_expenses_for_group(db, group_id)
    expense_with_relations = next((e for e in expenses if e.id == expense.id), expense)
    notify_group_members(
        background_tasks,
        group,
        {"type": "expenses_changed", "data": {"group_id": group_id}},
        exclude_user_ids=[current_user.id],
    )
    return serialize_expense(expense_with_relations)


@app.put("/api/groups/{group_id}/expenses/{expense_id}", response_model=ExpenseResponse)
def update_group_expense(
    group_id: int,
    expense_id: int,
    payload: ExpenseCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    expense = get_expense(db, expense_id)
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    payer, split_items, amount_cents = validate_expense_payload(group, payload)
    update_expense(
        db,
        expense,
        description=payload.description.strip(),
        amount_cents=amount_cents,
        paid_by_id=payer.id,
        splits=split_items,
    )
    updated = get_expense(db, expense_id) or expense
    notify_group_members(
        background_tasks,
        group,
        {"type": "expenses_changed", "data": {"group_id": group_id}},
        exclude_user_ids=[current_user.id],
    )
    return serialize_expense(updated)


@app.delete("/api/groups/{group_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_expense(
    group_id: int,
    expense_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    expense = get_expense(db, expense_id)
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    delete_expense(db, expense)
    notify_group_members(
        background_tasks,
        group,
        {"type": "expenses_changed", "data": {"group_id": group_id}},
        exclude_user_ids=[current_user.id],
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/groups/{group_id}/settlements", response_model=SettlementSummaryResponse)
def get_group_settlements(
    group_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    expenses = list_expenses_for_group(db, group_id)
    records = list_settlements_for_group(db, group_id)
    # Treat payer-confirmed settlements as affecting balances so recommendations shrink immediately.
    applied_records = [record for record in records if record.status in SETTLEMENT_APPLIED_STATUSES]
    recommendations = calculate_settlements(group, expenses, applied_records)
    return SettlementSummaryResponse(
        recommendations=recommendations,
        records=[serialize_settlement_record(record) for record in records],
    )


@app.post("/api/groups/{group_id}/settlements", response_model=SettlementRecordResponse, status_code=status.HTTP_201_CREATED)
def record_settlement_payment(
    group_id: int,
    payload: SettlementRecordRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    if payload.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount must be positive")

    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    member_map = {member.user.username: member.user for member in group.members if member.user}
    receiver = member_map.get(payload.receiver)
    if not receiver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver must be a group member")

    if receiver.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Receiver cannot be the same as payer")

    amount_cents = dollars_to_cents(payload.amount)
    settlement = create_settlement_record(
        db,
        group_id=group_id,
        payer_id=current_user.id,
        receiver_id=receiver.id,
        amount_cents=amount_cents,
    )
    notify_settlement_update(background_tasks, group_id, [current_user.id, receiver.id])
    return serialize_settlement_record(settlement)


@app.post("/api/groups/{group_id}/settlements/{settlement_id}/confirm", response_model=SettlementRecordResponse)
def confirm_settlement_payment(
    group_id: int,
    settlement_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    settlement = get_settlement(db, settlement_id)
    if not settlement or settlement.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")

    if settlement.receiver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the receiver can confirm")

    if settlement.status == "complete":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Settlement already confirmed")

    updated = confirm_settlement(db, settlement)
    notify_settlement_update(background_tasks, group_id, [settlement.payer_id, settlement.receiver_id])
    return serialize_settlement_record(updated)

@app.post("/api/groups/{group_id}/invite", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
def invite_user_to_group(
    group_id: int,
    payload: InviteCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    group = get_group_with_members(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if not any(member.user_id == current_user.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a member to invite others")

    target_username = payload.username.strip()
    if not target_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required")

    invitee = get_user_by_username(db, target_username)
    if not invitee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if any(member.user_id == invitee.id for member in group.members):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already in the group")

    if get_pending_invite(db, group_id=group.id, invitee_id=invitee.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already sent")

    invite = create_group_invite(db, group_id=group.id, inviter_id=current_user.id, invitee_id=invitee.id)
    invite = get_invite_by_id(db, invite.id) or invite
    payload_data = serialize_invite(invite)
    if background_tasks is not None:
        background_tasks.add_task(manager.send, invitee.id, {"type": "invite", "data": payload_data.dict()})
    return payload_data


@app.get("/api/invites", response_model=List[InviteResponse])
def list_invites(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    invites = list_pending_invites_for_user(db, current_user.id)
    return [serialize_invite(invite) for invite in invites]


@app.post("/api/invites/{invite_id}/accept", response_model=GroupResponse)
def accept_group_invite(
    invite_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invite = get_invite_by_id(db, invite_id)
    if not invite or invite.invitee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")

    if invite.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already processed")

    if not invite.group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    membership_exists = is_user_in_group(db, invite.group_id, current_user.id)
    if not membership_exists:
        db.add(GroupMember(group_id=invite.group_id, user_id=current_user.id))

    db.query(GroupInvite).filter(
        GroupInvite.group_id == invite.group_id,
        GroupInvite.invitee_id == invite.invitee_id,
        GroupInvite.status == "accepted",
        GroupInvite.id != invite.id,
    ).delete(synchronize_session=False)

    invite.status = "accepted"
    db.add(invite)
    db.commit()
    db.refresh(invite)

    group = get_group_with_members(db, invite.group_id)
    return serialize_group(group)


@app.get("/api/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        return {"error": "Not found"}
    return {"id": user.id, "username": user.username}


@app.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket):
    session_token = websocket.cookies.get("session")
    username = get_session_username(session_token)
    if not username:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        user = get_user_by_username(db, username)
        if not user:
            await websocket.close(code=4401)
            return

        await manager.connect(user.id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(user.id, websocket)
    finally:
        db.close()


if os.path.isfile(FRONTEND_INDEX):

    @app.get("/", include_in_schema=False)
    async def serve_frontend_root():
        return FileResponse(FRONTEND_INDEX)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_app(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return FileResponse(FRONTEND_INDEX)
 