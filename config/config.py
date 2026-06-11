"""Application configuration management."""

import os
from dotenv import load_dotenv
from enum import Enum

load_dotenv()

class ASRService(Enum):
    """Supported ASR (Automatic Speech Recognition) services."""
    PADDLESPEECH = "paddlespeech"
    BAIDU = "baidu"
    IFLYTEK = "iflytek"
    GOOGLE = "google"

class TTSService(Enum):
    """Supported TTS (Text-to-Speech) services."""
    EDGE_TTS = "edge-tts"
    BAIDU = "baidu"
    IFLYTEK = "iflytek"
    GOOGLE = "google"

class Config:
    """Base configuration class."""
    
    # Flask settings
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # ASR Configuration
    ASR_SERVICE = os.getenv("ASR_SERVICE", "paddlespeech").lower()
    ASR_API_KEY = os.getenv("ASR_API_KEY", "")
    ASR_LANGUAGE = os.getenv("ASR_LANGUAGE", "zh_CN")  # Chinese by default
    ASR_TIMEOUT = int(os.getenv("ASR_TIMEOUT", 30))
    
    # TTS Configuration
    TTS_SERVICE = os.getenv("TTS_SERVICE", "edge-tts").lower()
    TTS_API_KEY = os.getenv("TTS_API_KEY", "")
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "zh-CN")
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")  # Microsoft Edge TTS voice
    TTS_TIMEOUT = int(os.getenv("TTS_TIMEOUT", 30))
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", 16000))
    AUDIO_CHUNK_SIZE = int(os.getenv("AUDIO_CHUNK_SIZE", 1024))
    AUDIO_FORMAT = os.getenv("AUDIO_FORMAT", "wav")
    AUDIO_UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    
    # File Operation Configuration
    DEFAULT_DRIVES = os.getenv("DEFAULT_DRIVES", "C:,D:,E:,F:").split(",")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1024 * 1024 * 100))  # 100MB
    PROTECTED_PATHS = ["/System32", "/Windows", "/Program Files"]
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "app.log")
    
    # NLU Configuration
    NLU_CONFIDENCE_THRESHOLD = float(os.getenv("NLU_CONFIDENCE_THRESHOLD", 0.7))
    NLU_MAX_RETRIES = int(os.getenv("NLU_MAX_RETRIES", 3))
    
    @classmethod
    def init_directories(cls):
        """Initialize required directories."""
        os.makedirs(cls.AUDIO_UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    AUDIO_UPLOAD_FOLDER = "./test_uploads"

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

def get_config():
    """Get configuration based on environment."""
    env = os.getenv("FLASK_ENV", "development").lower()
    
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    
    return configs.get(env, DevelopmentConfig)
