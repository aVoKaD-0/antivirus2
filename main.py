from app.main import create_app
from migrations.database.main import PostgresDB
# from fastapi.staticfiles import StaticFiles
import subprocess

app = create_app()

if __name__ == "__main__":
    PostgresDB()
    subprocess.run([
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--reload"
    ])