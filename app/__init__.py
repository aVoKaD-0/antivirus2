import os
import json
import ijson
import datetime
import asyncio
from app.services.analysis_service import AnalysisService
# from app.repositories.file_repository import FileRepository
from app.utils.sse_operations import subscribers
from app.utils.logging import Logger
from app.utils.file_operations import FileOperations
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


class AnalysisResult(BaseModel):
    analysis_id: str
    result_data: dict

def create_app() -> FastAPI:
    app = FastAPI()
    analysis_service = AnalysisService()

    # Монтируем статические файлы
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        # Получаем историю пользователя
        history = FileOperations.load_user_history()

        return templates.TemplateResponse(
            "index.html",
            {"request": request, "history": history}
        )
    
    @app.get("/analysis/{analysis_id}")
    async def get_analysis_page(request: Request, analysis_id: str):
        try:
            history = FileOperations.load_user_history()
            analysis = next((item for item in history if item["analysis_id"] == analysis_id), None)
            if not analysis:
                return RedirectResponse(url="/")

            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "analysis_id": analysis_id,
                    "status": analysis["status"],
                    "file_activity": [],
                    "docker_output": "",
                    "history": history
                }
            )
        except Exception as e:
            Logger.log(f"Ошибка при получении страницы анализа: {str(e)}")
            return RedirectResponse(url="/")

    @app.post("/analyze")
    async def analyze_file(request: Request, file: UploadFile = File(...)):
        try:
            client_ip = FileOperations.get_client_ip
            user_upload_folder = FileOperations.user_upload

            FileOperations.user_file_upload(file=file, user_upload_folder=user_upload_folder)

            run_id = FileOperations.run_ID

            await analysis_service.analyze(run_id, file.filename, client_ip=client_ip)

            # Обновляем историю: сохраняем только analysis_id, filename, timestamp и status.
            history = Logger.load_user_history()
            history.append({
                "analysis_id": run_id,
                "filename": file.filename,
                "timestamp": datetime.now().isoformat(),
                "status": "running"
            })
            FileOperations.save_user_history(history)

            # Создаем пустую запись в results.json для хранения file_activity и docker_output.
            os.makedirs(os.path.join("results", run_id), exist_ok=True)
            results = FileOperations.load_user_results(run_id)
            FileOperations.save_user_results(results, run_id)

            Logger.log(f"Файл загружен и анализ запущен. ID анализа: {run_id}")
            
            return JSONResponse({
                "status": "success",
                "analysis_id": run_id
            })
        except Exception as e:
            (f"Ошибка при анализе файла: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/results/{analysis_id}")
    async def get_results(analysis_id: str):
        try:
            result_data = FileOperations.get_result_data(analysis_id)
            return JSONResponse(result_data)
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": str(e)})
    
    @app.get("/results/{analysis_id}/chunk")
    async def get_results_chunk(analysis_id: str, offset: int = 0, limit: int = 50):
        try:
            # Определяем путь к файлу результатов.
            # Предполагается, что результаты хранятся в файле data/{analysis_id}/results.json
            results_file = os.path.join("results", analysis_id, "results.json")
            if not os.path.exists(results_file):
                return JSONResponse(status_code=404, content={"detail": "Результаты не найдены"})

            chunk = []
            total = 0

            # Используем ijson для потокового парсинга ключа "file_activity", который должен быть массивом.
            # Это означает, что структура JSON должна быть примерно такой:
            # {
            #     "file_activity": [ {...}, {...}, ... ],
            #     "docker_output": "..."
            # }
            with open(results_file, "r", encoding="utf-8") as f:
                parser = ijson.items(f, "file_activity.item")
                for item in parser:
                    if total >= offset and len(chunk) < limit:
                        chunk.append(item)
                    total += 1

            return JSONResponse({
                "chunk": chunk,
                "offset": offset,
                "limit": limit,
                "total": total
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": str(e)})

    
    @app.get("/download/{analysis_id}", response_class=HTMLResponse)
    async def download_page(request: Request, analysis_id: str):
        # URL для скачивания файла
        download_url = f"/results/{analysis_id}/download"
        # Возвращаем простую HTML-страницу, которая через JavaScript перенаправляет пользователя на URL скачивания.
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Начало загрузки</title>
            <script>
                window.onload = function() {{
                    window.location.href = "{download_url}";
                }};
            </script>
        </head>
        <body>
            <p>Если загрузка не началась автоматически, нажмите <a href="{download_url}">здесь</a>.</p>
        </body>
        </html>
        """

    @app.get("/sse")
    async def sse_endpoint(request: Request):
        Logger.log("SSE endpoint called")
        async def event_generator():
            Logger.log("Event generator started")
            q = asyncio.Queue()
            subscribers.append(q)
            try:
                while True:
                    # Если клиент разорвал соединение, завершаем генерацию
                    if await request.is_disconnected():
                        Logger.log("Client disconnected")
                        break
                    # Ждем следующее событие
                    data = await q.get()
                    # Формируем SSE-сообщение (обратите внимание на формат)
                    Logger.log(f"Sending data: {data}")
                    yield f"data: {json.dumps(data)}\n\n"
            finally:
                Logger.log("Event generator finished")
                subscribers.remove(q)
        return EventSourceResponse(event_generator())

    @app.post("/submit-result/")
    async def submit_result(result: AnalysisResult):
        try:
            # Опционально: обновляем статус анализа в истории,
            # например, если в result_data передан новый статус.
            history = FileOperations.load_user_history()
            for entry in history:
                if entry["analysis_id"] == result.analysis_id:
                    entry["status"] = result.result_data.get("status", "completed")
                    break
            FileOperations.save_user_history(history)

            return {"status": "completed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app