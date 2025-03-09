import bcrypt
from domain.models.database import Users

class UserService:
    def __init__(self, db):
        self.db = db

    def create_user(self, username, email, password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = Users(username=username, email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        return user