from urllib.parse import quote_plus
from migrations.database.db.schemas import Base
from migrations.database.database import Database
from migrations.database.env import username, password, host, dbname


class PostgresDB():
    dsn = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"
    db = Database(dsn)
    Base.metadata.create_all(db.engine)