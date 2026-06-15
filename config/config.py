"""Application configuration management."""

import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

print("DEBUG: ASR_API_KEY =", os.getenv("ASR_API_KEY"))
print("DEBUG: BAIDU_SECRET_KEY =", os.getenv("BAIDU_SECRET_KEY"))

# 手动设置百度 API 凭证（也可放在 .env 文件里）
os.environ.setdefault("BAIDU_SECRET_KEY", "m81WLllJhuQUtWmzkwMMXuzuatJgNutd")
os.environ.setdefault("ASR_SERVICE", "baidu")
os.environ.setdefault("ASR_API_KEY", "N3HbMjyEYGD8S6a39MT7vOmL")
os.environ.setdefault("BAIDU_APP_ID", "7841848")

class ASRService(Enum):
    PADDLESPEECH = "paddlespeech"
    BAIDU = "baidu"
    IFLYTEK = "iflytek"
    GOOGLE = "google"

class TTSService(Enum):
    EDGE_TTS = "edge-tts"
    BAIDU = "baidu"
    IFLYTEK = "iflytek"
    GOOGLE = "google"

print("DEBUG: ASR_API_KEY =", os.getenv("ASR_API_KEY"))
print("DEBUG: BAIDU_SECRET_KEY =", os.getenv("BAIDU_SECRET_KEY"))

class Config:
    """Base configuration class."""

    # Flask settings
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # ASR Configuration
    ASR_SERVICE = os.getenv("ASR_SERVICE", "baidu").lower()
    ASR_API_KEY = os.getenv("ASR_API_KEY", "N3HbMjyEYGD8S6a39MT7vOmL")
    BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY", "")   # 关键修复
    ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "zh_CN")
    ASR_TIMEOUT = int(os.getenv("ASR_TIMEOUT", 30))

    # TTS Configuration
    TTS_SERVICE = os.getenv("TTS_SERVICE", "edge-tts").lower()
    TTS_API_KEY = os.getenv("TTS_API_KEY", "")
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "zh-CN")
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")
    TTS_TIMEOUT = int(os.getenv("TTS_TIMEOUT", 30))

    # Audio Configuration
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
    AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", 1024))
    AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")
    AUDIO_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")

    # File Operation Configuration
    DEFAULT_DRIVES = os.getenv("DEFAULT_DRIVES", "C:,D:,E:,F:").split(",")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1024 * 1024 * 100))
    PROTECTED_PATHS = ["/System32", "/Windows", "/Program Files"]

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "app.log")

    # NLU Configuration
    NLU_CONFIDENCE_THRESHOLD = float(os.getenv("NLU_CONFIDENCE_THRESHOLD", 0.7))
    NLU_MAX_RETRIES = int(os.getenv("NLU_MAX_RETRIES", 3))

    @classmethod
    def init_directories(cls):
        os.makedirs(cls.AUDIO_UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

# 如果不需要 get_config，可以忽略。但为了兼容保留
def get_config():
    env = os.getenv("FLASK_ENV", "development").lower()
    configs = {
        "development": Config,
        "testing": Config,
        "production": Config,
    }
    return configs.get(env, Config)()