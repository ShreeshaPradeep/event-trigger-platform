from app.models.user import User, UserCreate
from app.services.database import Database
from app.utils.auth import get_password_hash
from typing import Optional

class UserService:
    @staticmethod
    async def create_user(user: UserCreate) -> User:
        db = Database.get_db()
        hashed_password = get_password_hash(user.password)
        user_data = User(
            email=user.email,
            hashed_password=hashed_password
        )
        await db.users.insert_one(user_data.dict())
        return user_data

    @staticmethod
    async def get_user_by_email(email: str) -> Optional[User]:
        db = Database.get_db()
        user_data = await db.users.find_one({"email": email})
        return User(**user_data) if user_data else None 