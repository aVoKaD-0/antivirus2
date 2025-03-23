from app.repositories.file_repository import FileRepository
from app.utils.file_operations import FileOperations
from app.utils.logging import Logger
import os
import subprocess
import time
from app.infrastructure.repositories.analysis import docker, docker2
from app.services.db_service import AnalysisDbService
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from app.domain.models.database import get_db
from concurrent.futures import ThreadPoolExecutor
from app.utils.websocket_manager import manager
from app.services.user_service import UserService

# Получение учетных данных пользователя
username = "docker"
password = "docker"

class AnalysisService:
    def __init__(self, filename: str, analysis_id: str, uuid: str):
        self.db = None
        self.uuid = uuid
        self.filename = filename
        self.analysis_id = analysis_id 
        self.lock = asyncio.Lock()  # Создаем объект Lock


    def update_dockerfile(self):
        file = self.filename[:-4]
        print(file)
        dockerfile_content = f"""FROM mcr.microsoft.com/windows/servercore:ltsc2022
WORKDIR C:\\\\sandbox
COPY {self.filename} .
RUN powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force"
CMD ["powershell", "-command", "Start-Process -FilePath 'C:\\\\sandbox\\\\{self.filename}' -NoNewWindow -PassThru; Start-Sleep -Seconds 60"]
"""
        
        if not os.path.exists(f"{docker}\\{self.analysis_id}"):
            os.makedirs(f"{docker}\\{self.analysis_id}")
        
        with open(f"{docker}\\{self.analysis_id}\\Dockerfile", 'w') as dockerfile:
            dockerfile.write(dockerfile_content)

    def build_docker(self):
        print("Сборка Docker-образа...")
        subprocess.run(["powershell", "-command", f"docker build -t analysis_{self.analysis_id} -f {docker}\\{self.analysis_id}\\Dockerfile {docker}\\{self.analysis_id}\\"], check=True)

    async def run_in_executor(self, command):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(
                pool, 
                lambda: subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            )
        return result

    async def run_docker(self):
        print("Запуск контейнера...")
        command = ["powershell", "-command", f"docker run -it --isolation=process --name analysis_{self.analysis_id} analysis_{self.analysis_id}"]
        result = await self.run_in_executor(command)
        print("Контейнер успешно завершил работу.")
        await self.stop_etw()  # После завершения контейнера останавливаем ETW
        await self.get_file_changes()
        return

    async def get_docker_output(self):
        print("Получение логов...")
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", f"docker logs analysis_{self.analysis_id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

    async def run_etw(self):
        print("Запуск ETW для мониторинга файлов...")
        await asyncio.sleep(7)
        etw_command = ["powershell", "-command", f"xperf -on PROC_THREAD+LOADER+FILE_IO -f {docker}\\{self.analysis_id}\\trace.etl"]
        result = await self.run_in_executor(etw_command)
        print("ETW успешно запущен.")

    async def stop_etw(self):
        try:
            print("Остановка ETW...")
            command = ["powershell", "-command", "xperf -stop"]
            result = await self.run_in_executor(command)
            print("ETW успешно остановлен.")    
            await self.export_result()
        except Exception as e:
            print(f"Ошибка при остановке ETW: {str(e)}")

    async def export_result(self):
        print("Экспорт логов ETW...")
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", f"xperf -i {docker}\\{self.analysis_id}\\trace.etl -o {docker}\\{self.analysis_id}\\trace.txt",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

    async def run_procmon(self):
        print("Запуск Procmon...")
        procmon_command = f"""$container_pid = docker ps -q --filter 'ancestor=analysis_1'
procmon /Backingfile D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.pml /Filter 'PID is $container_pid Include'
"""
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", procmon_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        print("Procmon успешно запущен.")

    async def stop_procmon(self):
        try:
            print("Остановка Procmon...")
            process = await asyncio.create_subprocess_exec(
                "powershell", "-command", "procmon /Terminate",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            print("Procmon успешно остановлен.")
            await self.export_procmon()
        except Exception as e:
            print(f"Ошибка при остановке Procmon: {str(e)}")

    async def export_procmon(self):
        print("Экспорт логов Procmon...")
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", "procmon /OpenLog D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.pml /SaveAs D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.csv",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        print("Логи Procmon успешно экспортированы.")


    async def get_file_changes(self):
        print(f"📄 Отслеживание изменений файлов в контейнере analysis_{self.analysis_id}...")
        command = ["powershell", "-command", f"docker diff analysis_{self.analysis_id}"]
        result = await self.run_in_executor(command)
        changes = result.stdout.strip()

        await self.run_in_executor(["powershell", "-command", f"docker stop analysis_{self.analysis_id}"])
        await self.run_in_executor(["powershell", "-command", f"docker rm analysis_{self.analysis_id}"])

        if changes:
            print("🔍 Обнаружены изменения в файлах:\n", changes)
            changes_list = changes.splitlines()
            changes_output = []
            for change in changes_list:
                change_type = change[0]
                file_path = change[1:].strip()
                if change_type == 'C':
                    changes_output.append(f"Изменен: {file_path}")
                elif change_type == 'A':
                    changes_output.append(f"Добавлен: {file_path}")
                elif change_type == 'D':
                    changes_output.append(f"Удален: {file_path}")
            await self.lock.acquire()
            await Logger.save_file_activity(self.analysis_id, changes, self.db)
            await Logger.analysis_log("Анализ завершен успешно", self.analysis_id, self.db)
            self.lock.release()
            await manager.send_message(self.analysis_id, f"🔍 Обнаружены изменения в файлах")
            return 
        else:
            print("✅ Файлы не изменялись.")
            await self.lock.acquire()
            await Logger.save_file_activity(self.analysis_id, "Файлы не изменялись.", self.db)
            self.lock.release()
            return "Файлы не изменялись."

    async def analyze(self):
            try:   
                # Получаем сессию из асинхронного генератора
                async for db in get_db():
                    self.db = db
                    break  # Выходим из цикла после получения сессии
                print(self.db, "asd") 
                # await self.initialize_db()
                print("Запуск анализа...")
                print(self.db, "sfsd")
                await self.lock.acquire()
                await Logger.analysis_log("Анализ запущен", self.analysis_id, self.db)
                self.lock.release()
                print(123)
                self.update_dockerfile()
                self.build_docker()
                
                # Запускаем run_docker и run_etw параллельно
                asyncio.create_task(self.run_docker())
                asyncio.create_task(self.run_etw())
                # procmon_task = asyncio.create_task(self.run_procmon())
                

                # # Ожидаем завершения Procmon
                # await procmon_task
                
                # await self.stop_etw()
                # await self.export_result()
            except Exception as e:
                try:
                    await self.lock.acquire()
                    await Logger.update_history_on_error(self.analysis_id, "Анализ завершен с ошибкой", self.db)
                    self.lock.release()
                    self.stop_etw()
                    result = self.get_file_changes()
                    return result
                except Exception as e:
                    await self.lock.acquire() 
                    await Logger.update_history_on_error(self.analysis_id, e, self.db,)
                    self.lock.release()


    # # В функции завершения анализа
    # async def complete_analysis(analysis_id: str):
    #     # Логика завершения анализа
    #     await send_message(analysis_id, {"status": "completed"})