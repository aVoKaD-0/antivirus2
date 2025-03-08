import json
import os
from fastapi import Request
import os
import json
import ijson
import re
import time
import uuid
from shutil import rmtree, copyfileobj
from fastapi import Request
import subprocess
import csv
from app.utils.logging import Logger


project_dir = os.getcwd()[:os.getcwd().index("antivirus")].replace('\\', '\\')


class FileOperations:
    def user_upload(client_ip):
        return os.makedirs(os.path.join("uploads", client_ip), exist_ok=True)

    def user_file_upload(file, user_upload_folder):
        with open(os.path.join(user_upload_folder, file.filename), "wb") as buffer:
            copyfileobj(file.file, buffer)

    def run_ID():
        return str(uuid.uuid4())
    
    def load_user_history():
        history_file = "app/logs/history.json"
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8-sig") as file:
                return json.load(file)
        return []

    def save_user_history(history: list):
        history_dir = "app/logs"
        os.makedirs(history_dir, exist_ok=True)
        history_file = os.path.join(history_dir, "history.json")
        with open(history_file, "w") as file:
            json.dump(history, file, indent=4)

    def get_client_ip(request: Request):
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip = request.client.host
        return ip 
    
    def get_result_data(analysis_id: str) -> dict:
        results_file = os.path.join("results", analysis_id, "results.json")
        preview = []
        total = 0
        # Читаем только массив file_activity через ijson, чтобы избежать загрузки полного файла в память
        with open(results_file, "r", encoding="utf-8") as f:
            parser = ijson.items(f, "file_activity.item")
            for item in parser:
                if total < 100:
                    preview.append(item)
                total += 1

        docker_output = ""
        # Если docker_output находится в конце файла, читаем последние 100 КБ
        with open(results_file, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            read_size = 1000 * 1024  # 100 КБ
            start_pos = max(file_size - read_size, 0)
            f.seek(start_pos)
            tail = f.read().decode("utf-8", errors="replace")
            m = re.search(r'"docker_output"\s*:\s*"([^"]*)"', tail)
            if m:
                docker_output = m.group(1)

        result = {
            "file_activity": preview,
            "docker_output": docker_output,
            "total": total
        }
        return result
    
    def delete_vm(analysis_id):
        time.sleep(5)
        while True:
            try:
                rmtree(f"{project_dir}\\Hyper\\{analysis_id}")
                break
            except:
                Logger.global_log(f"Виртуальная машина {analysis_id} не удалена. Ожидание 5 секунд...", analysis_id)
                time.sleep(5)
        Logger.global_log(f"Виртуальная машина {analysis_id} удалена.", analysis_id)


    def get_client_ip(request: Request):
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0]
        else:
            ip = request.client.host
        return ip 
    
    # Функция ожидания запуска VM
    def wait_for_vm_running(vm_name, analysis_id, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            get_vm_command = f'Get-VM -Name "{vm_name}" | Select-Object -ExpandProperty State'
            try:
                state = subprocess.check_output(
                    ["powershell", "-Command", get_vm_command],
                    stderr=subprocess.STDOUT
                ).decode().strip()
                if state == "Running":
                    return True
            except subprocess.CalledProcessError as e:
                Logger.global_log(f"Ошибка при получении состояния VM: {e.output.strip()}", analysis_id)
            time.sleep(5)
        return False

    def export_procmon_logs(analysis_id, pml_file_path):
        results_dir = os.path.join("results", analysis_id)
        csv_file = os.path.join(results_dir, "procmon.csv")

        # Команда для экспорта логов из PML в CSV с использованием Procmon.exe.
        # Убедитесь, что Procmon.exe доступен (или задайте полный путь к нему).
        export_command = f'{project_dir}\\tools\\Procmon.exe /OpenLog "{pml_file_path}" /SaveAs "{csv_file}" /Quiet'
        try:
            Logger.global_log("Экспортируем логи Procmon в CSV...", analysis_id)
            subprocess.run(["powershell", "-Command", export_command], check=True)

            time.sleep(30)

            Logger.global_log("Конвертируем CSV в JSON...", analysis_id)
            activity = []
            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Process Name") != "Procmon64.exe" and row.get("Process Name") != "Procmon.exe":
                        activity.append(row)

            Logger.global_log("Сохраняем результаты в файл...", analysis_id)

            results_data = FileOperations.get_result_data(analysis_id)

            results_data["file_activity"] = activity

            FileOperations.save_results(results_data, analysis_id)
            Logger.global_log(f"Результаты сохранены в results_data", analysis_id)
            
            os.remove(f"{project_dir}\\results\\{analysis_id}\\procmon.csv")
            os.remove(f"{project_dir}\\results\\{analysis_id}\\procmon.pml")
            # Отправка результатов на сервер
            Logger.send_result_to_server(analysis_id, {"status": "completed"}, True)
            FileOperations.delete_vm(analysis_id)
        except Exception as e:
            Logger.global_log(f"Ошибка при экспорте логов Procmon: {e}", analysis_id)
            Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)}, False)
            FileOperations.delete_vm(analysis_id)