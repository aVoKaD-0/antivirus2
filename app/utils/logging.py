import json
import os
import requests
from loguru import logger
from app.repositories.file_repository import FileRepository
from migrations.database.db.models import Results, Analysis
from sqlalchemy import select
import uuid
from app.services.db_service import AnalysisDbService
# from app.auth.auth import uuid_by_token
from sqlalchemy.ext import asyncio

class Logger:
    # Добавляем лог в файл только один раз при старте
    logger.add("app/logs/GlobalLog.log", level="INFO", rotation="10 GB")

    @staticmethod
    def log(message):
        logger.info(message)
        return None

    @staticmethod
    async def analysis_log(msg, analysis_id, db):
        result = await AnalysisDbService().get_result(analysis_id, db)
        if result:
            result.docker_output += msg + "\n"
            await db.commit()
        return 
    
    @staticmethod
    async def save_result(analysis_id, result_data, db):
        print(result_data)
        result = await AnalysisDbService().get_result(analysis_id, db)
        if result:
            print(result)
            result.results = result_data
            await db.commit()
        return 
    
    @staticmethod
    async def save_file_activity(analysis_id, history, db):
        result = await AnalysisDbService().get_result(analysis_id, db)
        analysis = await AnalysisDbService().get_analysis(analysis_id, db)
        if result:
            analysis.status = "completed"
            result.file_activity = history
            await db.commit()
        return

    @staticmethod
    async def update_history_on_error(analysis_id, error_message, db):
        result = await AnalysisDbService().get_result(analysis_id, db)
        analysis = await AnalysisDbService().get_analysis(analysis_id, db)
        if analysis and result:
            analysis.status = "error"
            result.docker_output = error_message
            result.file_activity = ""
            await db.commit()
        return None

    @staticmethod
    def send_result_to_server(analysis_id, result_data):
        url = "http://192.168.31.153:8080/submit-result/"
        
        payload = {
            "analysis_id": analysis_id,
            "result_data": result_data
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                Logger.log(f"[{analysis_id}] ✅ Результаты отправлены на сервер")
            else:
                Logger.log(f"[{analysis_id}] ❌ Ошибка при отправке: {response.status_code}")
        except Exception as e:
            Logger.log(f"[{analysis_id}] ⚠️ Ошибка соединения: {str(e)}")
        return None