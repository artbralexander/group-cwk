from backend.crud.expenses import create_expense, list_expenses_for_group, get_expense, update_expense, delete_expense

def test_create_list_update_delete_expense(db, group, users):
    owner, bob, _ = users

    e = create_expense(
        db,
        group_id=group.id,
        description="Dinner",
        amount_cents=3000,
        paid_by_id=owner.id,
        category_id=None,
        splits=[
            {"user_id": owner.id, "amount_cents": 1500},
            {"user_id": bob.id, "amount_cents": 1500},
        ],
    )
    assert e.id is not None

    listed = list_expenses_for_group(db, group.id)
    assert len(listed) == 1
    assert listed[0].description == "Dinner"

    fetched = get_expense(db, e.id)
    assert fetched is not None
    assert len(fetched.splits) == 2

    updated = update_expense(
        db,
        fetched,
        description="Dinner (updated)",
        amount_cents=4000,
        paid_by_id=owner.id,
        category_id=None,
        splits=[
            {"user_id": owner.id, "amount_cents": 2000},
            {"user_id": bob.id, "amount_cents": 2000},
        ],
    )
    assert updated.description == "Dinner (updated)"
    assert get_expense(db, e.id).amount == 4000

    delete_expense(db, updated)
    assert get_expense(db, e.id) is None
