import os
import json
import asyncio
import subprocess
from app.utils.logging import Logger
from app.utils.websocket_manager import manager
from concurrent.futures import ThreadPoolExecutor
from app.infrastructure.repositories.analysis import docker

username = "docker"
password = "docker"

class AnalysisService:
    def __init__(self, filename: str, analysis_id: str, uuid: str):
        self.db = None
        self.uuid = uuid
        self.filename = filename
        self.analysis_id = analysis_id 
        self.lock = asyncio.Lock() 


    def update_dockerfile(self):
        file = self.filename[:-4]
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

    async def build_docker(self):
        await Logger.analysis_log("Сборка Docker-образа...", self.analysis_id)
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
        await Logger.analysis_log("Запуск контейнера...", self.analysis_id)
        command = ["powershell", "-command", f"docker run -it --isolation=process --name analysis_{self.analysis_id} analysis_{self.analysis_id}"]
        result = await self.run_in_executor(command)
        await Logger.analysis_log("Контейнер успешно завершил работу.", self.analysis_id)
        await self.stop_etw() 
        await self.get_file_changes()
        return

    async def get_docker_output(self):
        await Logger.analysis_log("Получение логов...", self.analysis_id)
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", f"docker logs analysis_{self.analysis_id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

    async def run_etw(self):
        await Logger.analysis_log("Запуск ETW для мониторинга файлов...", self.analysis_id)
        await asyncio.sleep(7)
        etw_command = ["powershell", "-command", f"xperf -on PROC_THREAD+LOADER+FILE_IO -f {docker}\\{self.analysis_id}\\trace.etl"]
        result = await self.run_in_executor(etw_command)
        await Logger.analysis_log("ETW успешно запущен.", self.analysis_id)

    async def stop_etw(self):
        try:
            await Logger.analysis_log("Остановка ETW...", self.analysis_id)
            command = ["powershell", "-command", "xperf -stop"]
            result = await self.run_in_executor(command)
            await Logger.analysis_log("ETW успешно остановлен.", self.analysis_id)    
            await self.export_result()
        except Exception as e:
            await Logger.analysis_log(f"Ошибка при остановке ETW: {str(e)}", self.analysis_id)

    async def export_result(self):
        await Logger.analysis_log("Экспорт логов ETW...", self.analysis_id)
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", f"xperf -i {docker}\\{self.analysis_id}\\trace.etl -o {docker}\\{self.analysis_id}\\trace.txt",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

    async def run_procmon(self):
        await Logger.analysis_log("Запуск Procmon...", self.analysis_id)
        procmon_command = f"""$container_pid = docker ps -q --filter 'ancestor=analysis_1'
procmon /Backingfile D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.pml /Filter 'PID is $container_pid Include'
"""
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", procmon_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        await Logger.analysis_log("Procmon успешно запущен.", self.analysis_id)

    async def stop_procmon(self):
        try:
            await Logger.analysis_log("Остановка Procmon...", self.analysis_id)
            process = await asyncio.create_subprocess_exec(
                "powershell", "-command", "procmon /Terminate",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            await Logger.analysis_log("Procmon успешно остановлен.", self.analysis_id)
            await self.export_procmon()
        except Exception as e:
            await Logger.analysis_log(f"Ошибка при остановке Procmon: {str(e)}", self.analysis_id)

    async def export_procmon(self):
        await Logger.analysis_log("Экспорт логов Procmon...", self.analysis_id)
        process = await asyncio.create_subprocess_exec(
            "powershell", "-command", "procmon /OpenLog D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.pml /SaveAs D:\\programming\\GIt\\gitlab\\antivirus\\dockerer\\1\\docker_log.csv",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        await Logger.analysis_log("Логи Procmon успешно экспортированы.", self.analysis_id)


    async def get_file_changes(self):
        await Logger.analysis_log(f"📄 Отслеживание изменений файлов в контейнере analysis_{self.analysis_id}...", self.analysis_id)
        command = ["powershell", "-command", f"docker diff analysis_{self.analysis_id}"]
        result = await self.run_in_executor(command)
        changes = result.stdout.strip()

        await self.run_in_executor(["powershell", "-command", f"docker stop analysis_{self.analysis_id}"])
        await self.run_in_executor(["powershell", "-command", f"docker rm analysis_{self.analysis_id}"])

        if changes:
            await Logger.analysis_log("🔍 Обнаружены изменения в файлах:\n", self.analysis_id)
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
            await Logger.save_file_activity(self.analysis_id, changes)
            await Logger.analysis_log("Анализ завершен успешно", self.analysis_id)
            self.lock.release()
            await manager.send_message(self.analysis_id, json.dumps({"status": "completed", "message": "🔍 Обнаружены изменения в файлах"}))
            return 
        else:
            Logger.analysis_log("✅ Файлы не изменялись.")
            await self.lock.acquire()
            await Logger.save_file_activity(self.analysis_id, "Файлы не изменялись.")
            await Logger.analysis_log("Анализ завершен успешно", self.analysis_id)
            self.lock.release()
            return "Файлы не изменялись."

    async def analyze(self):
            try:  
                await self.lock.acquire()
                await Logger.analysis_log("Анализ запущен", self.analysis_id)
                self.lock.release()
                self.update_dockerfile()
                self.build_docker()
                
                asyncio.create_task(self.run_docker())
                asyncio.create_task(self.run_etw())
            except Exception as e:
                try:
                    await self.lock.acquire()
                    await Logger.update_history_on_error(self.analysis_id, "Анализ завершен с ошибкой")
                    self.lock.release()
                    self.stop_etw()
                    result = self.get_file_changes()
                    return result
                except Exception as e:
                    await self.lock.acquire() 
                    await Logger.update_history_on_error(self.analysis_id, e)
                    self.lock.release()