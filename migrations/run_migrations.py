import os
import sys
import argparse
from alembic.config import Config
from alembic import command

# Получение абсолютного пути к текущей директории
base_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(base_dir)

# Добавление корневой директории проекта в sys.path
sys.path.append(project_dir)

def run_migrations(direction="upgrade", revision="head", version_path=None):
    """
    Запуск миграций Alembic.
    
    Args:
        direction (str): Направление миграции: "upgrade" или "downgrade"
        revision (str): Ревизия миграции (по умолчанию "head")
        version_path (str): Путь к директории с миграциями
    """
    # Создание конфигурации Alembic
    alembic_cfg = Config(os.path.join(project_dir, "alembic.ini"))
    
    # Если указана другая директория для миграций
    if version_path:
        alembic_cfg.set_main_option("script_location", version_path)
    
    # Запуск миграций
    if direction == "upgrade":
        print(f"Обновление базы данных до ревизии {revision}...")
        command.upgrade(alembic_cfg, revision)
    elif direction == "downgrade":
        print(f"Откат базы данных до ревизии {revision}...")
        command.downgrade(alembic_cfg, revision)
    elif direction == "init":
        print("Инициализация базы данных...")
        # Проверяем, существует ли файл ревизии
        command.upgrade(alembic_cfg, "head")
    
    print("Миграции успешно выполнены!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Утилита для запуска миграций базы данных")
    parser.add_argument("--direction", choices=["upgrade", "downgrade", "init"], default="upgrade",
                        help="Направление миграции: upgrade, downgrade или init")
    parser.add_argument("--revision", default="head",
                        help="Ревизия миграции (по умолчанию 'head')")
    parser.add_argument("--version-path", default=None,
                        help="Путь к директории с миграциями")
    
    args = parser.parse_args()
    run_migrations(args.direction, args.revision, args.version_path) 