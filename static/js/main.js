"""Main JavaScript for Voice Desktop Assistant.

Features:
- Audio recording and playback
- API communication
- Command execution
- UI state management
- History management
"""

// Global state
const state = {
    isRecording: false,
    mediaRecorder: null,
    audioContext: null,
    audioChunks: [],
    currentCommand: '',
    parsedCommand: null,
    isProcessing: false
};

// API endpoints
const API = {
    health: '/api/health',
    recognize: '/api/recognize',
    parse: '/api/parse',
    execute: '/api/execute',
    synthesize: '/api/synthesize',
    history: '/api/history',
    clearHistory: '/api/clear-history'
};

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('[App] Initializing Voice Desktop Assistant...');
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Check system health
    await checkSystemHealth();
    
    // Load history
    await loadHistory();
    
    console.log('[App] Initialization complete');
});

function initializeEventListeners() {
    """Setup all event listeners."""
    document.getElementById('recordBtn').addEventListener('click', startRecording);
    document.getElementById('stopBtn').addEventListener('click', stopRecording);
    document.getElementById('clearBtn').addEventListener('click', clearRecording);
    document.getElementById('executeBtn').addEventListener('click', executeCommand);
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);
    
    // Allow Enter key to execute in text input
    document.getElementById('commandInput').addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            executeCommand();
        }
    });
}

// ============================================================================
// System Health Check
// ============================================================================

async function checkSystemHealth() {
    """Check system health and engine availability."""
    try {
        const response = await fetch(API.health);
        const data = await response.json();
        
        updateStatus('systemStatus', data.status === 'healthy' ? '✅ 正常' : '❌ 异常');
        updateStatus('asrStatus', data.engines.asr === 'ready' ? '✅ 就绪' : '❌ 不可用');
        updateStatus('ttsStatus', data.engines.tts === 'ready' ? '✅ 就绪' : '❌ 不可用');
        
        console.log('[Health] System status:', data);
    } catch (error) {
        console.error('[Health] Check failed:', error);
        updateStatus('systemStatus', '❌ 无法连接');
        showToast('系统连接失败，请检查服务器', 'error');
    }
}

function updateStatus(elementId, status) {
    """Update status element."""
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = status;
    }
}

// ============================================================================
// Audio Recording
// ============================================================================

async function startRecording() {
    """Start audio recording."""
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Initialize media recorder
        state.mediaRecorder = new MediaRecorder(stream);
        state.audioChunks = [];
        state.isRecording = true;
        
        // Handle audio data
        state.mediaRecorder.ondataavailable = (event) => {
            state.audioChunks.push(event.data);
        };
        
        // Start recording
        state.mediaRecorder.start();
        
        // Update UI
        document.getElementById('recordBtn').disabled = true;
        document.getElementById('stopBtn').disabled = false;
        document.getElementById('recordingStatus').innerHTML = `
            <p style="color: #dc3545;">🔴 正在录音...</p>
        `;
        
        console.log('[Audio] Recording started');
    } catch (error) {
        console.error('[Audio] Recording failed:', error);
        showToast('无法访问麦克风，请检查权限', 'error');
    }
}

async function stopRecording() {
    """Stop audio recording and process."""
    if (!state.mediaRecorder) return;
    
    try {
        // Stop recording
        state.mediaRecorder.stop();
        state.isRecording = false;
        
        // Stop all audio tracks
        state.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        // Update UI
        document.getElementById('recordBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('recordingStatus').innerHTML = `
            <p style="color: #28a745;">✅ 录音完成，正在识别...</p>
        `;
        
        console.log('[Audio] Recording stopped');
        
        // Process audio
        await processRecordedAudio();
    } catch (error) {
        console.error('[Audio] Stop failed:', error);
        showToast('处理录音失败', 'error');
    }
}

function clearRecording() {
    """Clear recorded audio."""
    state.audioChunks = [];
    state.currentCommand = '';
    document.getElementById('commandInput').value = '';
    document.getElementById('recordingStatus').innerHTML = '<p>未开始录音</p>';
    console.log('[Audio] Recording cleared');
}

async function processRecordedAudio() {
    """Process recorded audio through ASR."""
    if (state.audioChunks.length === 0) {
        showToast('未录制任何音频', 'error');
        return;
    }
    
    try {
        // Combine audio chunks
        const audioBlob = new Blob(state.audioChunks, { type: 'audio/wav' });
        
        // Create form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('language', 'zh_CN');
        
        // Show loading
        showLoading(true, '正在识别语音...');
        
        // Send to ASR
        const response = await fetch(API.recognize, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        showLoading(false);
        
        if (data.success) {
            console.log('[ASR] Recognition result:', data);
            state.currentCommand = data.text;
            document.getElementById('commandInput').value = data.text;
            
            document.getElementById('recordingStatus').innerHTML = `
                <p style="color: #17a2b8;">识别结果: ${data.text}</p>
                <p style="color: #6c757d; font-size: 12px;">置信度: ${(data.confidence * 100).toFixed(1)}%</p>
            `;
            
            showToast('语音识别成功', 'success');
        } else {
            showToast('语音识别失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('[ASR] Error:', error);
        showLoading(false);
        showToast('语音识别错误: ' + error.message, 'error');
    }
}

// ============================================================================
// Command Processing
// ============================================================================

async function executeCommand() {
    """Execute the current command."""
    const command = document.getElementById('commandInput').value.trim();
    
    if (!command) {
        showToast('请输入或录制命令', 'warning');
        return;
    }
    
    if (state.isProcessing) {
        showToast('正在处理上一个命令，请稍候', 'warning');
        return;
    }
    
    state.isProcessing = true;
    state.currentCommand = command;
    
    try {
        // Show loading
        showLoading(true, '解析命令中...');
        
        // Parse command
        const parseResponse = await fetch(API.parse, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        const parseData = await parseResponse.json();
        console.log('[NLU] Parse result:', parseData);
        
        if (!parseData.success) {
            showLoading(false);
            showToast('命令解析失败: ' + parseData.message, 'error');
            state.isProcessing = false;
            return;
        }
        
        state.parsedCommand = parseData;
        displayCommandDetails(parseData);
        
        // Check if command is valid
        if (!parseData.is_valid) {
            showLoading(false);
            showToast('命令置信度过低，请重新说一遍', 'warning');
            state.isProcessing = false;
            return;
        }
        
        // Show loading for execution
        showLoading(true, '执行命令中...');
        
        // Execute command
        const execResponse = await fetch(API.execute, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        });
        
        const execData = await execResponse.json();
        console.log('[Execute] Result:', execData);
        
        // Hide loading
        showLoading(false);
        
        // Display result
        displayResult(execData);
        
        // Synthesize response
        await synthesizeResponse(execData.message);
        
        // Reload history
        await loadHistory();
        
        // Show toast
        if (execData.success) {
            showToast('命令执行成功', 'success');
        } else {
            showToast('命令执行失败: ' + execData.message, 'error');
        }
    } catch (error) {
        console.error('[Execute] Error:', error);
        showLoading(false);
        showToast('执行错误: ' + error.message, 'error');
    } finally {
        state.isProcessing = false;
    }
}

function displayCommandDetails(parseData) {
    """Display parsed command details."""
    const panel = document.getElementById('detailsPanel');
    
    document.getElementById('detailOperation').textContent = parseData.operation || '-';
    document.getElementById('detailFileType').textContent = parseData.file_type || '-';
    document.getElementById('detailSourceName').textContent = parseData.source_name || '-';
    document.getElementById('detailSourcePath').textContent = parseData.source_path || '-';
    document.getElementById('detailTargetPath').textContent = parseData.target_path || '-';
    document.getElementById('detailConfidence').textContent = 
        (parseData.confidence * 100).toFixed(1) + '%';
    
    panel.style.display = 'block';
}

function displayResult(execData) {
    """Display execution result."""
    const resultPanel = document.getElementById('resultPanel');
    const resultContent = document.getElementById('resultContent');
    
    const statusColor = execData.success ? '#28a745' : '#dc3545';
    const statusIcon = execData.success ? '✅' : '❌';
    
    let html = `
        <div class="result-status" style="color: ${statusColor}; margin-bottom: 15px;">
            <p style="font-size: 18px; font-weight: bold;">
                ${statusIcon} ${execData.message}
            </p>
        </div>
    `;
    
    if (execData.affected_items && execData.affected_items.length > 0) {
        html += `
            <div class="result-items" style="margin-top: 15px;">
                <h4>受影响的项目:</h4>
                <ul style="list-style-position: inside;">
        `;
        
        execData.affected_items.forEach(item => {
            html += `<li style="word-break: break-all; margin: 5px 0;">${item}</li>`;
        });
        
        html += `</ul></div>`;
    }
    
    if (execData.details) {
        html += `
            <div class="result-details" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd;">
                <h4>详细信息:</h4>
                <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow: auto;">${
                    JSON.stringify(execData.details, null, 2)
                }</pre>
            </div>
        `;
    }
    
    resultContent.innerHTML = html;
    resultPanel.style.display = 'block';
}

async function synthesizeResponse(text) {
    """Synthesize response text to speech."""
    try {
        const response = await fetch(API.synthesize, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            console.warn('[TTS] Synthesis failed');
            return;
        }
        
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        
        const audio = new Audio(audioUrl);
        audio.play().catch(err => console.warn('[Audio] Playback failed:', err));
        
        console.log('[TTS] Synthesis completed');
    } catch (error) {
        console.warn('[TTS] Error:', error);
    }
}

// ============================================================================
// History Management
// ============================================================================

async function loadHistory() {
    """Load and display operation history."""
    try {
        const response = await fetch(`${API.history}?limit=20`);
        const data = await response.json();
        
        if (!data.success || data.records.length === 0) {
            document.getElementById('historyContent').innerHTML = 
                '<p class="placeholder">暂无操作历史</p>';
            return;
        }
        
        let html = '<div class="history-items">';
        
        data.records.forEach((record, index) => {
            const statusIcon = record.success ? '✅' : '❌';
            const statusColor = record.success ? '#28a745' : '#dc3545';
            const time = new Date(record.timestamp).toLocaleTimeString('zh-CN');
            
            html += `
                <div class="history-item" style="border-left: 4px solid ${statusColor};">
                    <div class="history-time">${time}</div>
                    <div class="history-operation">${record.operation}</div>
                    <div class="history-command">${record.command}</div>
                    <div class="history-message" style="color: ${statusColor};">
                        ${statusIcon} ${record.message}
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        document.getElementById('historyContent').innerHTML = html;
        console.log('[History] Loaded', data.records.length, 'records');
    } catch (error) {
        console.error('[History] Load failed:', error);
    }
}

async function clearHistory() {
    """Clear operation history."""
    if (!confirm('确定要清除所有操作历史吗？')) return;
    
    try {
        showLoading(true, '清除中...');
        
        const response = await fetch(API.clearHistory, { method: 'POST' });
        const data = await response.json();
        
        showLoading(false);
        
        if (data.success) {
            await loadHistory();
            showToast('历史已清除', 'success');
        } else {
            showToast('清除失败: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('[History] Clear failed:', error);
        showLoading(false);
        showToast('清除错误: ' + error.message, 'error');
    }
}

// ============================================================================
// UI Utilities
// ============================================================================

function showLoading(show, text = '处理中...') {
    """Show or hide loading indicator."""
    const indicator = document.getElementById('loadingIndicator');
    const loadingText = document.getElementById('loadingText');
    
    if (show) {
        loadingText.textContent = text;
        indicator.classList.add('visible');
    } else {
        indicator.classList.remove('visible');
    }
}

function showToast(message, type = 'info') {
    """Show toast notification."""
    const toast = document.getElementById('toast');
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    toast.textContent = message;
    toast.style.backgroundColor = colors[type] || colors.info;
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

console.log('[App] Voice Desktop Assistant loaded successfully');
