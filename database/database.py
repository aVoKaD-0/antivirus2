from sqlalchemy import create_engine


class Database:
    def __init__(self, dsn):
        self.engine = create_engine(dsn)

    