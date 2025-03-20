from app.repositories.file_repository import FileRepository
from app.utils.file_operations import FileOperations
from app.utils.logging import Logger
import os
import subprocess
import time
from app.infrastructure.repositories.analysis import hyper
from app.services.db_service import AnalysisDbService

# Получение учетных данных пользователя
username = "docker"
password = "docker"

class AnalysisService:
    def __init__(self):
        self.db = None

    async def get_db(self):
        self.db = AnalysisDbService()
        await self.db.get_db()

    async def analyze(self, analysis_id, exe_filename, uuid):
        await Logger.analysis_log("Анализ файла начат", analysis_id, self.db)
        logs = ""
        try:
            await Logger.analysis_log(f"Импорт виртуальной машины с новым именем {analysis_id}", analysis_id, self.db)
            # os.path.join(hyper, "analysis_VMs", analysis_id, "Virtual Hard Disks")
            # import_vm_command = f"""
            # $vm = Import-VM -Path "{hyper}\\dock\\Virtual Machines\\118471C8-F8E1-4DF6-97A4-45D0FDF4C2D7.vmcx" -Copy -GenerateNewId -VirtualMachinePath "{hyper}\\analysis_VMs\\{analysis_id}" -VhdDestinationPath "{hyper}\\analysis_VMs\\{analysis_id}\\Virtual Hard Disks"
            # Rename-VM -VM $vm -NewName "{analysis_id}"
            # """
            # subprocess.run(["powershell", "-Command", import_vm_command], check=True)

            await Logger.analysis_log(f"Виртуальная машина импортирована как {analysis_id}.", analysis_id, self.db)

            diskcreate = f"""$pathdisk = "{hyper}\\temporary_disks\\{analysis_id}.vhdx"
                    # New-VHD -Path $pathdisk -SizeBytes 2GB -Dynamic
                    # Mount-VHD -Path $pathdisk
                    # $diskNumber = (Get-VHD -Path "$pathdisk").DiskNumber
                    # Initialize-Disk -Number $diskNumber
                    # New-Partition -DiskNumber $diskNumber -UseMaximumSize | Format-Volume -FileSystem NTFS -NewFileSystemLabel "SecureDisk"
                    # $partition = Get-Partition -DiskNumber $diskNumber
                    # $mainPartition = ($partition | Where-Object {{ $_.Type -eq "Basic" }})
                    # $guid = $mainPartition.Guid
                    # $path = "\\\\?\\Volume$($guid)\\"
                    # $securePassword = ConvertTo-SecureString -String "12345678" -AsPlainText -Force
                    # Enable-BitLocker -MountPoint "$path" -EncryptionMethod Aes256 -PasswordProtector -Password $securePassword
                    Add-VMHardDiskDrive -VMName "{analysis_id}" -Path $pathdisk
                    Dismount-VHD -Path $pathdisk
                    """
            
            subprocess.run(["powershell", "-Command", diskcreate], check=True)
            
            # Включение Guest Service Interface для VM
            await Logger.analysis_log(f"Включение Guest Service Interface для VM {analysis_id}", analysis_id, self.db)
            enable_guest_service_command = f"""
            Enable-VMIntegrationService -VMName "{analysis_id}" -Name "Интерфейс гостевой службы"
            """
            subprocess.run(["powershell", "-Command", enable_guest_service_command], check=True)
            await Logger.analysis_log("Guest Service Interface включен для виртуальной машины.", analysis_id, self.db)

            try:
                # Запуск виртуальной машины
                await Logger.analysis_log(f"Запуск виртуальной машины {analysis_id}", analysis_id, self.db)
                start_vm_command = f"""
                Start-VM -Name "{analysis_id}"
                """
                subprocess.run(["powershell", "-Command", start_vm_command], check=True)
                await Logger.analysis_log(f"Виртуальная машина {analysis_id} запущена.", analysis_id, self.db)
            except Exception as e:
                # Остановка виртуальной машины в случае ошибки
                await Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id, self.db)
                stop_vm_command = f"""
                Stop-VM -Name "{analysis_id}"
                Remove-VM -Name "{analysis_id}" -Force
                """
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                await Logger.analysis_log("VM остановлена", analysis_id, self.db)
                await Logger.analysis_log(f"Ошибка при запуске виртуальной машины: {str(e)}", analysis_id, self.db)
                await Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)})
                return

            # Ожидание запуска VM
            if not FileOperations.wait_for_vm_running(analysis_id, analysis_id):
                raise Exception(f"Виртуальная машина {analysis_id} не смогла запуститься в течение 300 секунд.", analysis_id)
            
            time.sleep(30)
            
            # Копирование файла в VM
            await Logger.analysis_log(f"Копирование файла в VM {analysis_id} {exe_filename}", analysis_id, self.db)
            copy_file_command = f"""
            Copy-VMFile -Name "{analysis_id}" -SourcePath "{hyper}\\files\\{uuid}\\{exe_filename}" -DestinationPath "C:\\Path\\InsideVM\\{exe_filename}" -CreateFullPath -FileSource Host
            Disable-VMIntegrationService -VMName "{analysis_id}" -Name "Интерфейс гостевой службы"
            """
            subprocess.run(["powershell", "-Command", copy_file_command], check=True)
            await Logger.analysis_log(f"Файл {exe_filename} успешно скопирован в виртуальную машину {analysis_id}.", analysis_id, self.db)
            
            await Logger.analysis_log(f"Настройка и запуск Procmon {analysis_id} {exe_filename}", analysis_id, self.db)
            local_procmon_path = f"{hyper}\\tools\\Procmon.exe"
            
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
                    # Создаём каталог для логов, если его нет
                    $logDir = Split-Path $logFile;
                    if (!(Test-Path $logDir)) {{
                        New-Item -ItemType Directory -Path $logDir -Force;
                    }}
                    Start-Process -FilePath $procmonPath -ArgumentList '/AcceptEula', '/Quiet', '/Minimized' -PassThru;
                }} else {{
                    Write-Output "Procmon.exe не найден.";
                }}
                Start-Sleep -Seconds 5
                Start-Process -FilePath "C:\\Path\\InsideVM\\{exe_filename}"
                Start-Sleep -Seconds 70
                C:\\Users\\docker\\Desktop\\procmon\\Procmon.exe /Terminate
                $diskNumber = 1
                $partition = Get-Partition -DiskNumber $diskNumber
                $mainPartition = ($partition | Where-Object {{ $_.Type -eq "Basic" }})
                $guid = $mainPartition.Guid
                $path = "\\\\?\\Volume$($guid)\\"
                $securePassword = ConvertTo-SecureString -String "12345678" -AsPlainText -Force
                Unlock-BitLocker -MountPoint "$path\\" -Password $securePassword
                Copy-Item -Path "C:\\Users\\docker\\Desktop\\logs\\procmon.pml" -Destination "E:\\" -Recurse -Force
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
                    await Logger.analysis_log(result.stdout.strip(), analysis_id, self.db)
                else:
                    await Logger.analysis_log(f"Ошибка при выполнении команды Procmon: {result.stderr.strip()}", analysis_id, self.db)
                    raise subprocess.CalledProcessError(result.returncode, setup_and_start_procmon_command, output=result.stdout, stderr=result.stderr)
            except subprocess.CalledProcessError as e:
                await Logger.analysis_log(f"Ошибка при выполнении команды Procmon: {e}", analysis_id, self.db)
                # Обновляем историю с ошибкой
                await Logger.update_history_on_error(analysis_id, str(e), self.db)
                raise

            result_copy = f"""
                    Remove-VMHardDiskDrive -VMName "{analysis_id}" -ControllerType IDE -ControllerNumber 0 -ControllerLocation 1
                    $pathdisk = "{hyper}\\temporary_disks\\{analysis_id}.vhdx"
                    Mount-VHD -Path $pathdisk
                    $diskNumber = (Get-VHD -Path "$pathdisk").DiskNumber
                    $partition = Get-Partition -DiskNumber $diskNumber
                    $mainPartition = ($partition | Where-Object {{ $_.Type -eq "Basic" }})
                    $guid = $mainPartition.Guid
                    $path = "\\\\?\\Volume$($guid)\\"
                    $securePassword = ConvertTo-SecureString -String "12345678" -AsPlainText -Force
                    Unlock-BitLocker -MountPoint "$path" -Password $securePassword
                    New-PSDrive -Name "TempDrive" -PSProvider FileSystem -Root "$path"
                    Copy-Item -Path "TempDrive:\\procmon.pml" -Destination "{hyper}\\results\\{analysis_id}.pml" -Recurse -Force
                    Remove-PSDrive -Name "TempDrive"
                    Dismount-VHD -Path $pathdisk
                    Remove-Item -Path $pathdisk
                    """
            
            subprocess.run(["powershell", "-Command", result_copy], check=True)

            # Остановка виртуальной машины
            await Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id, self.db)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                await Logger.analysis_log("VM остановлена", analysis_id, self.db)
            except subprocess.CalledProcessError as stop_e:
                await Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.decode().strip()}", analysis_id, self.db)

            # После завершения Procmon пробуем экспортировать лог
            results_dir = os.path.join("results", analysis_id)
            pml_file = os.path.join(results_dir, "procmon.pml")
            await FileOperations.export_procmon_logs(analysis_id, pml_file)
        except subprocess.CalledProcessError as e:
            await Logger.analysis_log(f"Ошибка при выполнении команды PowerShell: {str(e)}", analysis_id, self.db)
            # Остановка виртуальной машины
            await Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id, self.db)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                await Logger.analysis_log("VM остановлена", analysis_id, self.db)
            except subprocess.CalledProcessError as stop_e:
                await Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.strip()}", analysis_id, self.db)
            await Logger.analysis_log(f"Ошибка при запуске виртуальной машины: {str(e)}", analysis_id, self.db)
            await Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)})
            await Logger.update_history_on_error(analysis_id, logs + "\n" + str(e), self.db)
            FileOperations.delete_vm(analysis_id)
        except Exception as e:
            await Logger.analysis_log(f"Произошла ошибка: {str(e)}", analysis_id, self.db)
            # Остановка виртуальной машины
            await Logger.analysis_log(f"Остановка виртуальной машины {analysis_id}", analysis_id, self.db)
            stop_vm_command = f"""
            Stop-VM -Name "{analysis_id}" -Force
            Remove-VM -Name "{analysis_id}" -Force
            """
            try:
                subprocess.run(["powershell", "-Command", stop_vm_command], check=True)
                await Logger.analysis_log("VM остановлена", analysis_id, self.db)
            except subprocess.CalledProcessError as stop_e:
                await Logger.analysis_log(f"Ошибка при остановке VM: {stop_e.output.strip()}", analysis_id, self.db)
            await Logger.send_result_to_server(analysis_id, {"status": "error", "message": str(e)})
            await Logger.update_history_on_error(analysis_id, logs + "\n" + str(e), self.db)
            FileOperations.delete_vm(analysis_id)
