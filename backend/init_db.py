from db import engine
from models.user import User

User.metadata.create_all(bind=engine)
