import subprocess
from app.main import create_app
from migrations.database.main import PostgresDB

app = create_app()

if __name__ == "__main__":
    PostgresDB()
    subprocess.run([
        "uvicorn",
        "main:app",
        "--host", "192.168.31.153",
        "--port", "8080",
        "--reload"
    ])