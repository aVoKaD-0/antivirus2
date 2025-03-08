import json
import os
import requests
import logging
from app.repositories.file_repository import FileRepository


class Logger:
    def log(message):
        logging.basicConfig(filename="data/log.log")
        logging.info(msg=message)

    def analysis_log(msg, analysis_id):
        results_data = FileRepository.load_results(analysis_id)
        results_data["docker_output"] += msg + ";   "
        FileRepository.save_results(results_data, analysis_id)

    def update_history_on_error(analysis_id, error_message):
        history_file = "history/history.json"
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

    def send_result_to_server(analysis_id, result_data, success: bool):
        url = "http://localhost:8080/submit-result/"
        
        payload = {
            "analysis_id": analysis_id,
            "result_data": result_data
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                Logger.log(f"Результаты отправлены на сервер", analysis_id)
            else:
                Logger.log(f"Ошибка при отправке результатов: {response.status_code}", analysis_id)
        except Exception as e:
            Logger.log(f"Ошибка при отправке результатов: {str(e)}", analysis_id)