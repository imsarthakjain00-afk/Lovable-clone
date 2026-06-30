from src.utils.db import engine, Base
from src.Users.models import UserModel

Base.metadata.drop_all(engine)
print("All tables dropped successfully")
Base.metadata.create_all(engine)
print("Tables recreated successfully")
