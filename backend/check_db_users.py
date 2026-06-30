from src.utils.db import get_db
from src.Users.models import UserModel

db = next(get_db())
all_users = db.query(UserModel).all()
print(f"Total users in database: {len(all_users)}")
for user in all_users:
    print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
