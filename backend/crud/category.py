from sqlalchemy.orm import Session
from backend.models.group import GroupCategory, CategorySplit
from backend.models.user import User

def create_category(
        db: Session,
        *,
        group_id:int,
        name:str,
        description:str|None,
        budget: int,
        splits:list[dict]
):
    category = GroupCategory(group_id=group_id,name=name,description=description,budget=budget)
    db.add(category)
    db.flush()
    for split in splits:
        user = db.query(User).filter(User.username==split["username"]).first()
        if not user:
            raise ValueError("User not found")
        db.add(CategorySplit(category_id=category.id,user_id=user.id,share=split["share"]))
    db.commit()
    db.refresh(category)
    return category

def list_categories(db:Session, group_id:int):
    return(db.query(GroupCategory).filter(GroupCategory.group_id==group_id).all())


