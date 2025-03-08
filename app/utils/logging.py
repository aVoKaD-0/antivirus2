import json
import os
import requests
import logging
from loguru import logger
from app.repositories.file_repository import FileRepository


class Logger:
    # Добавляем лог в файл только один раз при старте
    logger.add("app/logs/GlobalLog.log", level="INFO", rotation="10 MB")

    @staticmethod
    def log(message):
        logger.info(message)

    @staticmethod
    def analysis_log(msg, analysis_id):
        results_data = FileRepository.get_result_data(analysis_id)
        results_data["docker_output"] += msg
        FileRepository.save_results(results_data, analysis_id)

    @staticmethod
    def update_history_on_error(analysis_id, error_message):
        history_file = "app/logs/history.json"
        if not os.path.exists(history_file):
            history = []
        else:
            with open(history_file, "r") as file:
                history = json.load(file)

        for entry in history:
            if entry["analysis_id"] == analysis_id:
                entry["status"] = "error"
                entry["file_activity"] = []
                entry["docker_output"] = error_message
                break

        with open(history_file, "w") as file:
            json.dump(history, file, indent=4)

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