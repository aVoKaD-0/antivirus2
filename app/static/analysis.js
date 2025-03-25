console.log("script.js loaded");

document.addEventListener('DOMContentLoaded', function() {
    const analysisId = window.analysisId;
    console.log("Global analysisId:", (typeof analysisId !== "undefined") ? analysisId : "undefined");

    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const progressBar = document.getElementById('progressBar');
    const progress = document.getElementById('progress');
    const resultsSection = document.getElementById('resultsSection');
    const analysisStatus = document.getElementById('analysisStatus');
    const dockerOutputContent = document.getElementById('dockerOutputContent');
    const statusSpinner = document.getElementById('statusSpinner');
    const refreshHistoryBtn = document.getElementById('refreshHistory');
    const token = localStorage.getItem('access_token');
    let fileActivityOffset = 0;
    const FILE_ACTIVITY_LIMIT = 500;
    let fileActivityTotal = 0;

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    async function handleFile(file) {
        console.log("Начало обработки файла:", file);
        progressBar.style.display = 'block';
        progress.style.width = '0%';
        resultsSection.style.display = 'block';
        statusSpinner.style.display = 'inline-block';
        analysisStatus.textContent = 'Загрузка файла...';
        console.log("все работает")

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log("Отправка файла...")
            const response = await fetch('/analysis/analyze', {
                method: 'POST',
                body: formData,
                headers: token ? {'Authorization': `Bearer ${token}`} : {}
            });
            console.log("Файл отправлен")

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Ошибка: ${response.status}`);
            }

            const data = await response.json();
            const runId = data.analysis_id;
            analysisStatus.textContent = 'Файл загружен. Открываем страницу анализа...';
            updateProgress(100);
            statusSpinner.style.display = 'none';

            console.log("Переходим на страницу /analysis/" + runId);
            window.location.href = `/analysis/analysis/${runId}`;
        } catch (error) {
            console.error('Error uploading file:', error);
            analysisStatus.textContent = 'Ошибка при загрузке файла: ' + error.message;
            analysisStatus.style.color = 'var(--error-color)';
            statusSpinner.style.display = 'none';
        }
    }

    function updateProgress(percent) {
        progress.style.width = `${percent}%`;
    }

    async function updateHistory() {
        try {
            const response = await fetch('/history');
            if (!response.ok) {
                throw new Error('Ошибка при получении истории');
            }
            const data = await response.json();
            const historyContainer = document.querySelector('.history-container');
            if (data.history && data.history.length) {
                historyContainer.innerHTML = '';
                data.history.forEach(item => {
                    const historyItem = document.createElement('div');
                    historyItem.classList.add('history-item');
                    if (item.status === 'running') {
                        historyItem.classList.add('running');
                    }
                    historyItem.setAttribute('data-analysis-id', item.analysis_id);
                    historyItem.innerHTML = `
                        <div class="history-item-header">
                            <span class="filename">${item.filename}</span>
                            <span class="timestamp">${item.timestamp}</span>
                        </div>
                        <div class="history-item-details">
                            <div class="status-indicator ${item.status}">${item.status}</div>
                            <button class="btn btn-sm btn-outline-secondary view-results-btn">Просмотреть результаты</button>
                        </div>
                    `;
                    historyContainer.appendChild(historyItem);
                });
                document.querySelectorAll('.view-results-btn').forEach(btn => {
                    btn.addEventListener('click', function(e) {
                        const analysisId = e.target.closest('.history-item').dataset.analysisId;
                        window.location.href = '/analysis/analysis/' + analysisId;
                    });
                });
            } else {
                historyContainer.innerHTML = '<p>История анализов пуста</p>';
            }
        } catch (error) {
            console.error('Ошибка обновления истории:', error);
        }
    }

    if (refreshHistoryBtn) {
        refreshHistoryBtn.addEventListener('click', updateHistory);
    }

    document.querySelectorAll('.view-results-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const analysisId = e.target.closest('.history-item').dataset.analysisId;
            window.location.href = '/analysis/analysis/' + analysisId;
        });
    });

    async function showResults(analysisId) {
        console.log("Показываем результаты анализа:", analysisId);
        try {
            const response = await fetch(`/analysis/results/${analysisId}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            console.log("Запрос отправлен")
            if (!response.ok) {
                console.log("Ошибка при получении результатов анализа:", response.status);
                if (response.status === 404) {
                    document.getElementById('fileActivityContent').textContent = 'Нет данных по файловой активности.';
                    document.getElementById('dockerOutputContent').textContent = 'Нет логов Docker.';
                    updateStatus('Нет данных');
                    return;
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            const data = await response.json();
            console.log("Получены результаты:", data);

            updateStatus(window.analysisStatus);
    
            console.log("Обработка file_activity как строки");
            console.log(data.file_activity);
            if (typeof data.file_activity === 'string' && data.file_activity.length > 0) {
                document.getElementById('fileActivityContent').textContent = data.file_activity;
            } else {
                document.getElementById('fileActivityContent').textContent = 'Нет данных по файловой активности.';
            }

            console.log("Обработка docker_output как строки");
    
            if (data.docker_output) {
                dockerOutputContent.textContent = data.docker_output;
            } else {
                dockerOutputContent.textContent = 'Нет логов Docker.';
            }
            const dockerLoader = document.getElementById('dockerOutputLoader');
            if (dockerLoader) dockerLoader.style.display = 'none';
    
            const loader = document.getElementById('fileActivityLoader');
            if (loader) loader.style.display = 'none';
        } catch (error) {
            console.error('Ошибка при получении результатов анализа:', error);
            analysisStatus.textContent = 'Ошибка при получении результатов анализа: ' + error.message;
            analysisStatus.style.color = 'var(--error-color)';
        }
    }

    function updateStatus(status) {
        const statusElement = document.getElementById('analysisStatus');
        console.log("Обновление статуса анализа:", status);
        statusElement.textContent = `Статус: ${status}`;
        if (status === 'completed') {
            statusElement.style.color = 'var(--success-color)';
            statusSpinner.style.display = 'none';
        } else if (status === 'running') {
            statusElement.style.color = 'var(--warning-color)';
            statusSpinner.style.display = 'inline-block';
        } else {
            statusElement.style.color = 'var(--error-color)';
            statusSpinner.style.display = 'none';
        }
    }

    async function loadNextChunk(analysisId, limitOverride) {
        try {
            const limit = limitOverride !== undefined ? limitOverride : FILE_ACTIVITY_LIMIT;
            const response = await fetch(`analysis/results/${analysisId}/chunk?offset=${fileActivityOffset}&limit=${limit}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const pre = document.getElementById('fileActivityContent');
            const existingContent = pre.textContent;
            const newContent = JSON.stringify(data.chunk, null, 4);
            pre.textContent = existingContent + "\n" + newContent;
            fileActivityOffset += data.chunk.length;
            updateLoadMoreButton(analysisId);
        } catch (error) {
            console.error('Ошибка при загрузке чанка:', error);
        }
    }

    function downloadFullFile(analysisId) {
        window.location.assign(`analysis/download/${analysisId}`);
    }

    function updateLoadMoreButton(analysisId) {
        const container = document.getElementById('fileActivityContainer');
        let buttonArea = document.getElementById('buttonArea');
        if (!buttonArea) {
            buttonArea = document.createElement('div');
            buttonArea.id = 'buttonArea';
            buttonArea.style.display = 'flex';
            buttonArea.style.gap = '10px';
            buttonArea.style.marginTop = '10px';
            container.appendChild(buttonArea);
        }
        buttonArea.innerHTML = "";

        if (fileActivityTotal > fileActivityOffset) {
            const loadMoreBtn = document.createElement('button');
            loadMoreBtn.id = 'loadMoreBtn';
            loadMoreBtn.textContent = 'Загрузить ещё';
            loadMoreBtn.className = 'btn btn-secondary';
            loadMoreBtn.addEventListener('click', function() {
                loadNextChunk(analysisId);
            });
            buttonArea.appendChild(loadMoreBtn);

            const loadAllBtn = document.createElement('button');
            loadAllBtn.id = 'loadAllBtn';
            loadAllBtn.textContent = 'Загрузить всё';
            loadAllBtn.className = 'btn btn-primary';
            loadAllBtn.addEventListener('click', function() {
                downloadFullFile(analysisId);
            });
            buttonArea.appendChild(loadAllBtn);
        }
        const remaining = fileActivityTotal - fileActivityOffset;
        const remainingSpan = document.getElementById('remainingCount');
        if (remainingSpan) {
            remainingSpan.textContent = "Осталось элементов: " + remaining;
        }
    }
    var x = window.A;
    console.log(x);

    if (typeof analysisId !== "undefined" && analysisId) {
        console.log("Загружаем результаты анализа:", analysisId);
        showResults(analysisId);
        // setInterval(() => {
        //     updateDockerLogs(analysisId);
        // }, 5000);
    }

    // async function updateDockerLogs(analysisId) {
    //     try {
    //         const response = await fetch(`/results/${analysisId}`, {
    //             headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    //         });
    //         if (!response.ok) {
    //             console.error("Ошибка при получении логов докера:", response.status);
    //             return;
    //         }
    //         const data = await response.json();
    //         if (data.docker_output) {
    //             dockerOutputContent.textContent = data.docker_output;
    //         } else {
    //             dockerOutputContent.textContent = 'Нет логов Docker.';
    //         }
    //         updateStatus("completed");
    //         const dockerLoader = document.getElementById('dockerOutputLoader');
    //         if (dockerLoader) dockerLoader.style.display = 'none';
    //     } catch (error) {
    //         console.error("Ошибка при обновлении логов докера:", error);
    //     }
    // }


    if (analysisId) {
        const ws = new WebSocket(`ws://${window.location.host}/analysis/ws/${analysisId}`);
        ws.onopen = function() {
            console.log("WebSocket connection established");
        };
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            if (data.status === 'completed') {
                location.reload();  
            }
        };
        ws.onclose = function() {
            console.log("WebSocket connection closed");
        };
        ws.onerror = function(error) {
            console.error("WebSocket Error:", error);
        };
    }

    document.getElementById('profileIcon').addEventListener('click', function() {
        const logoutBtn = document.getElementById('logoutBtnProfile');
        const changePasswordBtn = document.getElementById('changePasswordBtn');
        if (logoutBtn.style.display === 'none') {
            logoutBtn.style.display = 'block';
            changePasswordBtn.style.display = 'block';
        } else {
            logoutBtn.style.display = 'none';
            changePasswordBtn.style.display = 'none';
        }
    });

    document.getElementById('logoutBtnProfile').addEventListener('click', function() {
        console.log('Выход из аккаунта');
        fetch('/users/logout', {
            method: 'POST',
            credentials: 'include'
        }).then(response => {
            if (response.ok) {
                window.location.href = '/'; 
            }
        });
    });

    document.getElementById('changePasswordBtn').addEventListener('click', function() {
        window.location.href = '/users/reset-password';
    });
});