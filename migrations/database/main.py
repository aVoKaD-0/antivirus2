from migrations.database.database import Database
from migrations.database.db.schemas import Base
from urllib.parse import quote_plus
from migrations.database.db.models import Analysis, Results
from migrations.database.env import username, password, host, dbname
from app.domain.models.user import Users


class PostgresDB():
    dsn = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"
    db = Database(dsn)

    # Создание всех таблиц
    Base.metadata.create_all(db.engine)