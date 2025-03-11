from database.database import Database
from database.db.schemas import Base
from urllib.parse import quote_plus
from database.db.models import Users, Analysis, Results
from database.env import username, password, host, dbname


class PostgresDB():
    dsn = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"
    db = Database(dsn)

    # Создание всех таблиц
    Base.metadata.create_all(db.engine)