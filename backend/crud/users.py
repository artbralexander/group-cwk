from sqlalchemy.orm import Session
from backend.models.user import User


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, username: str, email: str, password_hash: str):
    user = User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    *,
    email: str | None = None,
    password_hash: str | None = None,
):
    if email is not None:
        user.email = email
    if password_hash is not None:
        user.password_hash = password_hash

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
