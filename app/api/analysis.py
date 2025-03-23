import os
import json
import ijson
import datetime
import asyncio
import uuid
from app.services.analysis_service import AnalysisService
# from app.repositories.file_repository import FileRepository
from app.utils.sse_operations import subscribers
from app.utils.logging import Logger
from app.utils.file_operations import FileOperations
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, UploadFile, File, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.schemas.analysis import AnalysisRequest
from app.auth.auth import uuid_by_token
from app.domain.models.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.services.db_service import AnalysisDbService


router = APIRouter(prefix="/analysis", tags=["analysis"])
# analysis_service = AnalysisService()

router.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# @router.get("/protected")
# async def protected_route(username: str = Depends(get_current_user)):
#     return {"message": f"Hello, {username}!"}

@router.get("/", response_class=HTMLResponse)
async def root(request: Request, db: AsyncSession = Depends(get_db)):
    userservice = UserService(db)
    # Получаем историю пользователя
    history = await userservice.get_user_analyses(uuid_by_token(request.cookies.get("refresh_token")))

    return templates.TemplateResponse(
        "analisys.html",
        {"request": request, "history": history}
    )

@router.get("/analysis/{analysis_id}")
async def get_analysis_page(request: Request, analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        userservice = UserService(db)

        history = await userservice.get_user_analyses(uuid_by_token(request.cookies.get("refresh_token")))
        
        # Получаем данные анализа
        analysis_data = await userservice.get_result_data(str(analysis_id))
        if not analysis_data:
            return RedirectResponse(url="/")

        return templates.TemplateResponse(
            "analisys.html",
            {
                "request": request,
                "analysis_id": str(analysis_id),
                "status": analysis_data.get("status", "unknown"),
                "file_activity": analysis_data.get("file_activity", []),
                "docker_output": analysis_data.get("docker_output", ""),
                "history": history
            }
        )
    except Exception as e:
        Logger.log(f"Ошибка при получении страницы анализа: {str(e)}")
        return RedirectResponse(url="/")

@router.post("/analyze")
async def analyze_file(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        userservice = UserService(db)
        refresh_token = request.cookies.get("refresh_token")
        uuid = uuid_by_token(refresh_token)
        run_id = FileOperations.run_ID()

        upload_folder = FileOperations.user_upload(str(run_id))
        if not upload_folder:
            raise HTTPException(status_code=500, detail="Не удалось создать директорию для загрузки")
        
        FileOperations.user_file_upload(file=file, user_upload_folder=upload_folder)

        await userservice.create_analysis(uuid, file.filename, str(run_id), "running", run_id)

        await userservice.create_result(run_id)

        analysis_service = AnalysisService(file.filename, str(run_id), str(uuid))

        asyncio.create_task(analysis_service.analyze())

        Logger.log(f"Файл загружен и анализ запущен. ID анализа: {run_id}")
        
        return JSONResponse({
            "status": "running",
            "analysis_id": str(run_id)
        })
    except Exception as e:
        Logger.log(f"Ошибка при анализе файла: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{analysis_id}")
async def get_results(analysis_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        print(str(analysis_id))
        userservice = UserService(db)
        result_data = await userservice.get_result_data(str(analysis_id))
        print("ok")
        return JSONResponse(result_data)
    except Exception as e:
        print("NOT OK")
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/results/{analysis_id}/chunk")
async def get_results_chunk(analysis_id: uuid.UUID, offset: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    try:
        userservice = UserService(db)
        result, total = await userservice.get_chunk_result(str(analysis_id), offset, limit)
        return JSONResponse({
            "chunk": result,
            "offset": offset,
            "limit": limit,
            "total": total
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@router.get("/download/{analysis_id}", response_class=HTMLResponse)
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

# @router.get("/sse")
# async def sse_endpoint(request: Request):
#     Logger.log("SSE endpoint called")
#     async def event_generator():
#         Logger.log("Event generator started")
#         q = asyncio.Queue()
#         subscribers.routerend(q)
#         try:
#             while True:
#                 # Если клиент разорвал соединение, завершаем генерацию
#                 if await request.is_disconnected():
#                     Logger.log("Client disconnected")
#                     break
#                 # Ждем следующее событие
#                 data = await q.get()
#                 # Формируем SSE-сообщение (обратите внимание на формат)
#                 Logger.log(f"Sending data: {data}")
#                 yield f"data: {json.dumps(data)}\n\n"
#         finally:
#             Logger.log("Event generator finished")
#             subscribers.remove(q)
#     return EventSourceResponse(event_generator())

@router.post("/submit-result/")
async def submit_result(result: AnalysisRequest):
    try:
        await FileOperations.save_result(result.analysis_id, result.result_data)
        return {"status": "completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))