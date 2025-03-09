from app.main import create_app
from database.main import PostgresDB

app = create_app()

if __name__ == "__main__":
    import uvicorn
    PostgresDB()
    uvicorn.run(app, host="192.168.31.153", port=8080) 