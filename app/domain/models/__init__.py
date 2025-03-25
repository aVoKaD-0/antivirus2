# Импортируем все модели для регистрации в SQLAlchemy
from app.domain.models.user import Users
from migrations.database.db.models import Analysis, Results

# Объединяем все модели для удобного импорта
__all__ = ['Users', 'Analysis', 'Results'] 