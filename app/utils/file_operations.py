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
from app.infrastructure.repositories.analysis import hyper
from app.services.db_service import AnalysisDbService
from migrations.database.db.models import Analysis, Results
from sqlalchemy.sql import func, text, select
from app.infrastructure.repositories.analysis import hyper


project_dir = os.getcwd()[:os.getcwd().index("antivirus")].replace('\\', '\\')+"antivirus2"


class FileOperations:
    @staticmethod
    def user_upload(email):
        upload_path = os.path.join(hyper, "files", email)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path  # Возвращаем путь к директории

    @staticmethod
    def user_file_upload(file, user_upload_folder):
        if not user_upload_folder:
            raise ValueError("Путь для загрузки файла не указан")
            
        file_path = os.path.join(user_upload_folder, file.filename)
        with open(file_path, "wb") as buffer:
            copyfileobj(file.file, buffer)

    def run_ID():
        return uuid.uuid4()
    
    @staticmethod
    async def get_user_analyses(user_id: str):
        db_service = AnalysisDbService()
        return await db_service.get_user_analyses(user_id)
    
    @staticmethod
    async def get_analysis_details(analysis_id: str):
        db_service = AnalysisDbService()
        return await db_service.get_result(analysis_id)
    
    @staticmethod
    async def get_chunk_result(analysis_id: str, offset: int = 0, limit: int = 50):
        db_service = AnalysisDbService()
        async with await db_service.get_db() as session:
            result = await session.execute(
                text(f"""
                    SELECT jsonb_path_query_array(
                        file_activity,
                        '$.items[{offset} to {offset + limit - 1}]'
                    )
                    FROM results
                    WHERE analysis_id = :analysis_id
                """),
                {"analysis_id": analysis_id}
            )
            total = await session.execute(
                text("""
                    SELECT jsonb_array_length(file_activity)
                    FROM results
                    WHERE analysis_id = :analysis_id
                """),
                {"analysis_id": analysis_id}
            )
            return result.scalar(), total.scalar()

    @staticmethod
    async def save_user_history(analysis_id: str, history: list):
        db = AnalysisDbService()
        await db.save_activity(analysis_id, history)

    # def get_client_ip(request: Request):
    #     if request.headers.get('X-Forwarded-For'):
    #         ip = request.headers.get('X-Forwarded-For').split(',')[0]
    #     else:
    #         ip = request.client.host
    #     return ip 

    @staticmethod
    async def create_analysis(user_id: str, filename: str, timestamp: str, status: str, analysis_id: uuid.UUID):
        db_service = AnalysisDbService()
        analysis = Analysis(
            user_id=user_id, 
            filename=filename, 
            timestamp=timestamp, 
            status=status, 
            analysis_id=analysis_id
        )
        return await db_service.add(analysis)
    
    @staticmethod
    async def create_result(analysis_id: uuid.UUID, file_activity: str, docker_output: str, results: str):
        db_service = AnalysisDbService()
        result = Results(
            analysis_id=analysis_id, 
            file_activity=file_activity, 
            docker_output=docker_output, 
            results=results
        )
        return await db_service.add(result)
    
    @staticmethod
    async def get_result_data(analysis_id: str) -> dict:
        db_service = AnalysisDbService()
        async with await db_service.get_db() as session:
            result = await session.execute(
                select(Results).filter(Results.analysis_id == analysis_id)
            )
            result_obj = result.scalars().first()
            
            analysis = await session.execute(
                select(Analysis).filter(Analysis.analysis_id == analysis_id)
            )
            analysis_obj = analysis.scalars().first()
            
            if not result_obj and not analysis_obj:
                return {
                    "status": "unknown",
                    "file_activity": [],
                    "docker_output": "",
                    "total": 0
                }
            
            return {
                "status": analysis_obj.status if analysis_obj else "unknown",
                "file_activity": result_obj.file_activity if result_obj and result_obj.file_activity else [],
                "docker_output": result_obj.docker_output if result_obj and result_obj.docker_output else "",
                "total": result_obj.results if result_obj and result_obj.results else 0
            }
    
    @staticmethod
    async def save_result(analysis_id: str, file_activity: str):
        db_service = AnalysisDbService()
        await db_service.save_activity(analysis_id, file_activity)

    def delete_vm(analysis_id):
        time.sleep(5)
        while True:
            try:
                rmtree(f"{hyper}\\analysis_VMs\\{analysis_id}")
                break
            except:
                Logger.log(f"Виртуальная машина {analysis_id} не удалена. Ожидание 5 секунд...", analysis_id)
                time.sleep(5)
        Logger.log(f"Виртуальная машина {analysis_id} удалена.", analysis_id)


    # def get_client_ip(request: Request):
    #     if request.headers.get('X-Forwarded-For'):
    #         ip = request.headers.get('X-Forwarded-For').split(',')[0]
    #     else:
    #         ip = request.client.host
    #     return ip 
    
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
                Logger.log(f"Ошибка при получении состояния VM: {e.output.strip()}", analysis_id)
            time.sleep(5)
        return False

    async def export_procmon_logs(analysis_id, pml_file_path):
        results_dir = os.path.join(hyper, "results", analysis_id)
        csv_file = os.path.join(results_dir, "procmon.csv")

        # Команда для экспорта логов из PML в CSV с использованием Procmon.exe.
        # Убедитесь, что Procmon.exe доступен (или задайте полный путь к нему).
        export_command = f'{hyper}\\tools\\Procmon.exe /OpenLog "{pml_file_path}" /SaveAs "{csv_file}" /Quiet'
        try:
            Logger.log("Экспортируем логи Procmon в CSV...", analysis_id)
            await subprocess.run(["powershell", "-Command", export_command], check=True)

            # time.sleep(30)

            Logger.log("Конвертируем CSV в JSON...", analysis_id)
            activity = []
            with open(csv_file, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Process Name") != "Procmon64.exe" and row.get("Process Name") != "Procmon.exe":
                        activity.append(row)

            Logger.log("Сохраняем результаты в файл...", analysis_id)

            FileOperations.save_results(analysis_id, activity)
            Logger.log(f"Результаты сохранены в activitety", analysis_id)
            
            os.remove(f"{project_dir}\\results\\{analysis_id}\\procmon.csv")
            os.remove(f"{project_dir}\\results\\{analysis_id}\\procmon.pml")
            # Отправка результатов на сервер
            Logger.send_result_to_server(analysis_id, {"status": "completed"})
            FileOperations.delete_vm(analysis_id)
        except Exception as e:
            Logger.log(f"Ошибка при экспорте логов Procmon: {e}", analysis_id)
            Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)})
            FileOperations.delete_vm(analysis_id)