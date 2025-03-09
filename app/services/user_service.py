class UserService:
    def __init__(self, db):
        self.db = db

    def create_user(self, username, email, hashed_password):
        user = User(username=username, email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        return user