from backend.crud.users import get_user_by_username, get_user_by_email, update_user, create_user

def test_create_and_get_user(db):
    u = create_user(db, "maad", "maad@example.com", "hash")
    assert u.id is not None

    assert get_user_by_username(db, "maad").id == u.id
    assert get_user_by_email(db, "maad@example.com").id == u.id

def test_update_user_email(db):
    u = create_user(db, "sam", "sam@example.com", "hash")
    u2 = update_user(db, u, email="sam2@example.com")
    assert u2.email == "sam2@example.com"
