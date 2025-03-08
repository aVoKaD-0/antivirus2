from app.repositories.file_repository import FileRepository
from app.utils.file_operations import project_dir, FileOperations
from app.utils.logging import Logger
import os
import subprocess
import time

# Получение учетных данных пользователя
username = "docker"
password = "docker"

class AnalysisService:
    def __init__(self):
        self.file_repo = FileRepository()
        self.logger = Logger()

    async def analyze(self, analysis_id, exe_filename, client_ip):
        self.logger.analysis_log("Анализ файла начат")
        logs = ""
        try:
            Logger.analysis_log(f"Импорт виртуальной машины с новым именем {analysis_id}", analysis_id)
            os.path.join(project_dir, "Hyper", analysis_id, "Virtual Hard Disks")
            import_vm_command = f"""
            $vm = Import-VM -Path "{project_dir}\\Hyper\\ExportedVM\\dock2\\dock\\Virtual Machines\powershell\DBC8697E-E08F-48FB-9E7A-60FCFC763752.vmcx" -Copy -GenerateNewId -VirtualMachinePath "{project_dir}\\Hyper\\{analysis_id}" -VhdDestinationPath "{project_dir}\\Hyper\\{analysis_id}\\Virtual Machines";
            Rename-VM -VM $vm -NewName "{analysis_id}";
            """
            subprocess.run(["powershell", "-Command", import_vm_command], check=True)
            Logger.analysis_log(f"Виртуальная машина импортирована как {analysis_id}.", analysis_id)

            Logger.analysis_log(f"Виртуальная машина {analysis_id} создана.", analysis_id)

            # Включение Guest Service Interface для VM
            Logger.analysis_log(f"Включение Guest Service Interface для VM {analysis_id}", analysis_id)
            enable_guest_service_command = f"""
            Enable-VMIntegrationService -VMName "{analysis_id}" -Name "Интерфейс гостевой службы"
            """
            subprocess.run(["powershell", "-Command", enable_guest_service_command], check=True)
            Logger.analysis_log("Guest Service Interface включен для виртуальной машины.", analysis_id)

            try:
                # Запуск виртуальной машины
                Logger.analysis_log(f"Запуск виртуальной машины {analysis_id}", analysis_id)
                start_vm_command = f"""
                Start-VM -Name "{analysis_id}"
                """
                subprocess.run(["powershell", "-Command", start_vm_command], check=True)
                Logger.analysis_log(f"Виртуальная машина {analysis_id} запущена.", analysis_id)
            except Exception as e:
                # Остановка виртуальной машины в случае ошибки
                Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id)
                stop_vm_command = f"""
                Stop-VM -Name "{analysis_id}"
                Remove-VM -Name "{analysis_id}" -Force
                """
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                Logger.analysis_log("VM остановлена", analysis_id)
                Logger.analysis_log(f"Ошибка при запуске виртуальной машины: {str(e)}", analysis_id)
                Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)}, False)
                return

            # Ожидание запуска VM
            if not FileOperations.wait_for_vm_running(analysis_id, analysis_id):
                raise Exception(f"Виртуальная машина {analysis_id} не смогла запуститься в течение 300 секунд.", analysis_id)
            
            # Копирование файла в VM
            Logger.analysis_log(f"Копирование файла в VM {analysis_id} {exe_filename}", analysis_id)
            copy_file_command = f"""
            Copy-VMFile -Name "{analysis_id}" -SourcePath "{project_dir}\\uploads\\{client_ip}\\{exe_filename}" -DestinationPath "C:\\Path\\InsideVM\\{exe_filename}" -CreateFullPath -FileSource Host
            """
            subprocess.run(["powershell", "-Command", copy_file_command], check=True)
            Logger.analysis_log(f"Файл {exe_filename} успешно скопирован в виртуальную машину {analysis_id}.", analysis_id)

            Logger.analysis_log(f"Настройка и запуск Procmon {analysis_id} {exe_filename}", analysis_id)
            local_procmon_path = f"{project_dir}\\tools\\Procmon.exe"
            
            # Проверка существования файла Procmon на хосте
            if not os.path.exists(local_procmon_path):
                raise FileNotFoundError(f"Procmon.exe не найден по пути {local_procmon_path}")

            setup_and_start_procmon_command = f"""
            $secpasswd = ConvertTo-SecureString "{password}" -AsPlainText -Force;
            $credential = New-Object System.Management.Automation.PSCredential ("{username}", $secpasswd);
            $session = New-PSSession -VMName "{analysis_id}" -Credential $credential;
            Invoke-Command -Session $session -ScriptBlock {{
                $procmonPath = "C:\\Users\\docker\\Desktop\\procmon\\Procmon.exe";
                $logFile = "C:\\Users\\docker\\Desktop\\logs\\procmon.pml";
                if (Test-Path $procmonPath) {{
                    Write-Output "Procmon.exe найден.";
                    # Создаём каталог для логов, если его нет
                    $logDir = Split-Path $logFile;
                    if (!(Test-Path $logDir)) {{
                        New-Item -ItemType Directory -Path $logDir -Force;
                    }}
                    Start-Process -FilePath $procmonPath -ArgumentList '/AcceptEula', '/Quiet', '/Minimized' -PassThru;
                    Write-Output "Procmon запущен с логированием в $logFile";
                }} else {{
                    Write-Output "Procmon.exe не найден.";
                }}
                Write-Output "Ожидание 5 секунд..."
                Start-Sleep -Seconds 5
                Write-Output "Запуск {exe_filename}..."
                Start-Process -FilePath "C:\\Path\\InsideVM\\{exe_filename}"
                Write-Output "Ожидание 70 секунд..."
                Start-Sleep -Seconds 70
                Write-Output "Остановка Procmon..."
                C:\\Users\\docker\\Desktop\\procmon\\Procmon.exe /Terminate
                Write-Output "Procmon остановлен."
            }};
            Remove-PSSession $session;
            """
            try:
                result = subprocess.run(
                    ["powershell", "-Command", setup_and_start_procmon_command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    Logger.analysis_log(result.stdout.strip(), analysis_id)
                else:
                    Logger.analysis_log(f"Ошибка при выполнении команды Procmon: {result.stderr.strip()}", analysis_id)
                    raise subprocess.CalledProcessError(result.returncode, setup_and_start_procmon_command, output=result.stdout, stderr=result.stderr)
            except subprocess.CalledProcessError as e:
                Logger.analysis_log(f"Ошибка при выполнении команды Procmon: {e}", analysis_id)
                # Обновляем историю с ошибкой
                Logger.update_history_on_error(analysis_id, str(e))
                raise

            Logger.analysis_log("ожидаем Procmon", analysis_id)
            time.sleep(10)

            # Проверка завершения Procmon
            wait_process_command = f"""
            $proc = Get-Process -Name "procmon" -ErrorAction SilentlyContinue
            while ($proc) {{
                Start-Sleep -Seconds 1
                $proc = Get-Process -Name "procmon" -ErrorAction SilentlyContinue
            }}
            Write-Output "Procmon завершен."
            """
            try:
                result = subprocess.run(
                    ["powershell", "-Command", wait_process_command],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    Logger.analysis_log(result.stdout.strip(), analysis_id)
                else:
                    Logger.analysis_log(f"Ошибка при ожидании завершения Procmon: {result.stderr.strip()}", analysis_id)
                    raise subprocess.CalledProcessError(result.returncode, wait_process_command, output=result.stdout, stderr=result.stderr)
            except subprocess.CalledProcessError as e:
                Logger.analysis_log(f"Ошибка при ожидании завершения Procmon: {e}", analysis_id)
                # Обновляем историю с ошибкой
                Logger.update_history_on_error(analysis_id, str(e))
                raise

            # Копирование логов на хост с механизмом повторных попыток
            Logger.analysis_log(f"Копирование логов на хост {analysis_id} {exe_filename}", analysis_id)
            logs_destination = os.path.join(project_dir, "results", analysis_id, "procmon.pml")
            os.makedirs(os.path.dirname(logs_destination), exist_ok=True)

            copy_logs_command = f"""
            $secpasswd = ConvertTo-SecureString "{password}" -AsPlainText -Force;
            $credential = New-Object System.Management.Automation.PSCredential ("{username}", $secpasswd);
            $log_file_path = "C:\\Users\\docker\\Desktop\\logs\\procmon.pml";
            $logs_destination = "{logs_destination}";
            $s = New-PSSession -VMName "{analysis_id}" -Credential $credential;
            Copy-Item -Path "$log_file_path" -Destination "$logs_destination" -FromSession $s
            """

            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                try:
                    subprocess.run(["powershell", "-Command", copy_logs_command], check=True, capture_output=True, text=True)
                    Logger.analysis_log("Логи Procmon скопированы на хост.", analysis_id)
                    break  # Если копирование прошло успешно, выходим из цикла
                except subprocess.CalledProcessError as e:
                    Logger.analysis_log(f"Попытка {attempt} копирования завершилась неудачно: {e}. Файл может быть ещё заблокирован.", analysis_id)
                    if attempt == max_attempts:
                        Logger.analysis_log("Превышено число попыток копирования файла. Завершаем процесс.", analysis_id)
                        Logger.update_history_on_error(analysis_id, str(e))
                        raise
                    else:
                        time.sleep(5)  # Ждем 5 секунд перед следующей попыткой

            # Остановка виртуальной машины
            Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                Logger.analysis_log("VM остановлена", analysis_id)
            except subprocess.CalledProcessError as stop_e:
                Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.decode().strip()}", analysis_id)

            # После завершения Procmon пробуем экспортировать лог
            results_dir = os.path.join("results", analysis_id)
            pml_file = os.path.join(results_dir, "procmon.pml")
            FileOperations.export_procmon_logs(analysis_id, pml_file)
        except subprocess.CalledProcessError as e:
            Logger.analysis_log(f"Ошибка при выполнении команды PowerShell: {str(e)}", analysis_id)
            # Остановка виртуальной машины
            Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                Logger.analysis_log("VM остановлена", analysis_id)
            except subprocess.CalledProcessError as stop_e:
                Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.strip()}", analysis_id)
            Logger.analysis_log(f"Ошибка при запуске виртуальной машины: {str(e)}", analysis_id)
            Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)}, False)
            Logger.update_history_on_error(analysis_id, logs + "\n" + str(e))
            FileOperations.delete_vm(analysis_id)
        except Exception as e:
            Logger.analysis_log(f"Произошла ошибка: {str(e)}", analysis_id)
            # Остановка виртуальной машины
            Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                Logger.analysis_log("VM остановлена", analysis_id)
            except subprocess.CalledProcessError as stop_e:
                Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.strip()}", analysis_id)
            Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)}, False)
            Logger.update_history_on_error(analysis_id, logs + "\n" + str(e))
            FileOperations.delete_vm(analysis_id)
