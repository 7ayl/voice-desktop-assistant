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
from pydub import AudioSegment  # 确保导入

from config.config import Config
from modules import (
    ASREngine, TTSEngine, NLUEngine, FileOperator, setup_logger
)

config = Config()
config.init_directories()

logger = setup_logger(__name__)

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

operation_history = []

def require_engines(f):
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
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
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'message': '未上传音频文件'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'message': '音频文件为空'}), 400

        audio_data = audio_file.read()
        if len(audio_data) == 0:
            return jsonify({'success': False, 'message': '音频数据为空'}), 400

        # ========== 音频格式转换（强制 16-bit PCM WAV） ==========
        try:
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            wav_io = io.BytesIO()
            audio_segment.export(wav_io, format='wav', parameters=["-acodec", "pcm_s16le"])
            audio_data = wav_io.getvalue()
            logger.info(f"Audio converted to 16kHz mono 16-bit WAV, size: {len(audio_data)} bytes")
        except Exception as e:
            logger.warning(f"Audio conversion failed, using original data: {str(e)}")
        # ========================================================

        language = request.form.get('language', Config.ASR_LANGUAGE)
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
        return jsonify({'success': False, 'message': f'语音识别失败: {str(e)}'}), 500

@app.route('/api/parse', methods=['POST'])
@require_engines
def parse_command():
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'success': False, 'message': '未提供命令文本'}), 400
        command = data['command'].strip()
        if not command:
            return jsonify({'success': False, 'message': '命令文本为空'}), 400
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
        return jsonify(result)
    except Exception as e:
        logger.error(f"Command parsing error: {str(e)}")
        return jsonify({'success': False, 'message': f'命令解析失败: {str(e)}'}), 500

@app.route('/api/execute', methods=['POST'])
@require_engines
def execute_command():
    try:
        data = request.get_json()
        if not data or 'command' not in data:
            return jsonify({'success': False, 'message': '未提供命令文本'}), 400
        command = data['command'].strip()
        parsed = nlu_engine.parse(command)
        result = file_operator.execute(parsed)
        operation_history.append({
            'timestamp': datetime.now().isoformat(),
            'command': command,
            'operation': result['operation'],
            'success': result['success'],
            'message': result['message']
        })
        return jsonify(result)
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return jsonify({'success': False, 'message': f'命令执行失败: {str(e)}'}), 500

@app.route('/api/synthesize', methods=['POST'])
@require_engines
def synthesize_speech():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'message': '未提供合成文本'}), 400
        text = data['text'].strip()
        if not text:
            return jsonify({'success': False, 'message': '合成文本为空'}), 400
        audio_data = tts_engine.synthesize(text)
        audio_io = io.BytesIO(audio_data)
        return send_file(audio_io, mimetype='audio/mpeg', as_attachment=True, download_name=f'output_{datetime.now().timestamp()}.mp3')
    except Exception as e:
        logger.error(f"Text synthesis error: {str(e)}")
        return jsonify({'success': False, 'message': f'文本合成失败: {str(e)}'}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        offset = int(request.args.get('offset', 0))
        records = operation_history[-offset-limit:-offset] if offset else operation_history[-limit:]
        records.reverse()
        return jsonify({'success': True, 'total': len(operation_history), 'records': records})
    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}")
        return jsonify({'success': False, 'message': f'获取历史失败: {str(e)}'}), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    global operation_history
    count = len(operation_history)
    operation_history = []
    return jsonify({'success': True, 'message': f'已清除 {count} 条历史记录', 'cleared_count': count})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': '请求的资源不存在', 'error': '404'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'success': False, 'message': '服务器内部错误', 'error': '500'}), 500

if __name__ == '__main__':
    logger.info("Starting Voice Desktop Assistant...")
    logger.info(f"Environment: {Config.FLASK_ENV}")
    logger.info(f"Debug mode: {Config.DEBUG}")
    app.run(host='0.0.0.0', port=5005, debug=Config.DEBUG, threaded=True)