from database import Database
from db.schemas import Base
from urllib.parse import quote_plus
from db.models import Users, Analysis, Results


username = "postgres"
password = "postgres"
host = "localhost"
port = "5432"
dbname = "antivirus"

dsn = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}/{dbname}"
db = Database(dsn)

# Создание всех таблиц
Base.metadata.create_all(db.engine)