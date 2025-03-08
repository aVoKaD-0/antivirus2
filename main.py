from app.main import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.31.153", port=8080) 