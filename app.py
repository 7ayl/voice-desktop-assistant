"""Flask application for Voice Desktop Assistant.

Main application entry point with API routes for:
- Audio recording and speech recognition
- Command parsing and execution
- Text-to-speech synthesis
- Operation logging and history
"""

import os
import io
import json
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config.config import get_config, Config
from modules import (
    ASREngine, TTSEngine, NLUEngine, FileOperator, setup_logger
)

# Initialize configuration
config = get_config()
config.init_directories()

# Setup logger
logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)
CORS(app)

# Initialize AI modules
try:
    asr_engine = ASREngine()
    logger.info("ASR Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ASR Engine: {str(e)}")
    asr_engine = None

try:
    tts_engine = TTSEngine()
    logger.info("TTS Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize TTS Engine: {str(e)}")
    tts_engine = None

try:
    nlu_engine = NLUEngine()
    logger.info("NLU Engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize NLU Engine: {str(e)}")
    nlu_engine = None

try:
    file_operator = FileOperator()
    logger.info("File Operator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize File Operator: {str(e)}")
    file_operator = None

# Operation history for user feedback
operation_history = []

def require_engines(f):
    """Decorator to check if required engines are initialized."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not all([asr_engine, tts_engine, nlu_engine, file_operator]):
            return jsonify({
                'success': False,
                'message': '系统初始化未完成，部分AI引擎不可用',
                'missing_engines': [
                    'ASR' if not asr_engine else '',
                    'TTS' if not tts_engine else '',
                    'NLU' if not nlu_engine else '',
                    'FileOperator' if not file_operator else ''
                ]
            }), 503
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# Routes
# ============================================================================

@app.route('/')
def index():
    """Serve main application page."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'engines': {
            'asr': 'ready' if asr_engine else 'unavailable',
            'tts': 'ready' if tts_engine else 'unavailable',
            'nlu': 'ready' if nlu_engine else 'unavailable',
            'file_operator': 'ready' if file_operator else 'unavailable'
        }
    })

@app.route('/api/recognize', methods=['POST'])
@require_engines
def recognize_speech():
    """Recognize speech from uploaded audio file.
    
    Request:
        - audio: Binary audio data (WAV format recommended)
        - language: Optional language code (default: zh_CN)
    
    Response:
        {
            'success': bool,
            'text': str,  # Recognized text
            'confidence': float,  # Recognition confidence
            'timestamp': str  # ISO timestamp
        }
    """
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'message': '未上传音频文件'
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'success': False,
                'message': '音频文件为空'
            }), 400
        
        # Read audio data
        audio_data = audio_file.read()
        if len(audio_data) == 0:
            return jsonify({
                'success': False,
                'message': '音频数据为空'
            }), 400
        
        # Get language
        language = request.form.get('language', Config.ASR_LANGUAGE)
        
        # Perform ASR
        logger.info(f"Recognizing speech, audio size: {len(audio_data)} bytes")
        recognized_text, confidence = asr_engine.recognize(audio_data, language)
        
        logger.info(f"Recognition result: '{recognized_text}' (confidence: {confidence})")
        
        return jsonify({
            'success': True,
            'text': recognized_text,
            'confidence': float(confidence),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Speech recognition error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'语音识别失败: {str(e)}'
        }), 500

@app.route('/api/parse', methods=['POST'])
@require_engines
def parse_command():
    """Parse user command and extract intent/parameters.
    
    Request:
        {
            'command': str  # User command text
        }
    
    Response:
        {
            'success': bool,
            'operation': str,
            'file_type': str,
            'source_name': str,
            'source_path': str,
            'target_name': str,
            'target_path': str,
            'confidence': float,
            'is_valid': bool
        }
    """
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({
                'success': False,
                'message': '未提供命令文本'
            }), 400
        
        command = data['command'].strip()
        if not command:
            return jsonify({
                'success': False,
                'message': '命令文本为空'
            }), 400
        
        # Parse command
        logger.info(f"Parsing command: {command}")
        parsed = nlu_engine.parse(command)
        
        result = {
            'success': True,
            'operation': parsed.operation.value,
            'file_type': parsed.file_type.value,
            'source_name': parsed.source_name,
            'source_path': parsed.source_path,
            'target_name': parsed.target_name,
            'target_path': parsed.target_path,
            'confidence': float(parsed.confidence),
            'is_valid': parsed.is_valid(),
            'raw_command': parsed.raw_command
        }
        
        logger.info(f"Parsing result: {result}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Command parsing error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'命令解析失败: {str(e)}'
        }), 500

@app.route('/api/execute', methods=['POST'])
@require_engines
def execute_command():
    """Execute file operation based on parsed command.
    
    Request:
        {
            'command': str  # Original user command (for logging)
        }
    
    Response:
        {
            'success': bool,
            'message': str,
            'operation': str,
            'affected_items': List[str],
            'details': dict
        }
    """
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({
                'success': False,
                'message': '未提供命令文本'
            }), 400
        
        command = data['command'].strip()
        
        # Parse command
        parsed = nlu_engine.parse(command)
        
        # Execute operation
        logger.info(f"Executing operation: {parsed.operation.value}")
        result = file_operator.execute(parsed)
        
        # Add to history
        operation_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'operation': result['operation'],
            'success': result['success'],
            'message': result['message']
        })
        
        logger.info(f"Execution result: {result['message']}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'命令执行失败: {str(e)}'
        }), 500

@app.route('/api/synthesize', methods=['POST'])
@require_engines
def synthesize_speech():
    """Synthesize text to speech.
    
    Request:
        {
            'text': str,  # Text to synthesize
            'language': str,  # Optional language code
            'voice': str  # Optional voice name
        }
    
    Response:
        Audio file binary data
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': '未提供合成文本'
            }), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({
                'success': False,
                'message': '合成文本为空'
            }), 400
        
        # Synthesize
        logger.info(f"Synthesizing text: {text[:50]}...")
        audio_data = tts_engine.synthesize(text)
        
        logger.info(f"Synthesis completed, audio size: {len(audio_data)} bytes")
        
        # Return audio as response
        audio_io = io.BytesIO(audio_data)
        return send_file(
            audio_io,
            mimetype='audio/mpeg',  # Edge TTS returns MP3
            as_attachment=True,
            download_name=f'output_{datetime.now().timestamp()}.mp3'
        )
    
    except Exception as e:
        logger.error(f"Text synthesis error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'文本合成失败: {str(e)}'
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get operation history.
    
    Query parameters:
        - limit: Maximum number of records (default: 50)
        - offset: Number of records to skip (default: 0)
    
    Response:
        {
            'success': bool,
            'total': int,
            'records': List[dict]
        }
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        
        records = operation_history[-offset-limit:-offset] if offset else operation_history[-limit:]
        records.reverse()  # Show most recent first
        
        return jsonify({
            'success': True,
            'total': len(operation_history),
            'records': records
        })
    
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        }), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear operation history."""
    try:
        global operation_history
        count = len(operation_history)
        operation_history = []
        
        logger.info(f"Cleared {count} history records")
        return jsonify({
            'success': True,
            'message': f'已清除 {count} 条历史记录',
            'cleared_count': count
        })
    
    except Exception as e:
        logger.error(f"History clearing error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清除历史失败: {str(e)}'
        }), 500

# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'message': '请求的资源不存在',
        'error': '404'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'message': '服务器内部错误',
        'error': '500'
    }), 500

# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting Voice Desktop Assistant...")
    logger.info(f"Environment: {Config.FLASK_ENV}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    
    # Start Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG,
        threaded=True
    )
