"""Automatic Speech Recognition (ASR) Engine Module.

Supports multiple ASR services:
- PaddleSpeech (local, free)
- Baidu Cloud (cloud-based)
- iFlytek (cloud-based, Chinese optimized)
- Google Cloud (cloud-based)
"""

import os
import io
import wave
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from .logger import setup_logger
from config.config import Config, ASRService

logger = setup_logger(__name__)

class ASRBase(ABC):
    """Abstract base class for ASR engines."""
    
    def __init__(self, api_key: Optional[str] = None, language: str = "zh_CN"):
        """Initialize ASR engine.
        
        Args:
            api_key: API key for cloud-based services
            language: Language code (e.g., 'zh_CN', 'en_US')
        """
        self.api_key = api_key
        self.language = language
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
        
    @abstractmethod
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Recognize speech from audio data.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Tuple of (recognized_text, confidence_score)
            
        Raises:
            Exception: If recognition fails
        """
        pass
    
    def _validate_audio(self, audio_data: bytes) -> bool:
        """Validate audio data format.
        
        Args:
            audio_data: Audio bytes to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not audio_data or len(audio_data) < 100:
            logger.warning("Audio data too short")
            return False
        return True

class PaddleSpeechASR(ASRBase):
    """PaddleSpeech ASR implementation (offline, free)."""
    
    def __init__(self, language: str = "zh_CN"):
        """Initialize PaddleSpeech ASR.
        
        Args:
            language: Language code ('zh_CN' for Chinese, 'en_US' for English)
        """
        super().__init__(api_key=None, language=language)
        
        try:
            # Lazy import to avoid loading model on startup
            from paddlespeech.cli.asr import ASRExecutor
            self.executor = ASRExecutor()
            logger.info("PaddleSpeech ASR engine initialized")
        except ImportError:
            logger.error("PaddleSpeech not installed. Install with: pip install paddlespeech")
            self.executor = None
    
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Recognize speech using PaddleSpeech.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        if not self._validate_audio(audio_data):
            raise ValueError("Invalid audio data")
        
        if self.executor is None:
            raise RuntimeError("PaddleSpeech engine not available")
        
        try:
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Recognize
            result = self.executor(
                audio_file=temp_path,
                lang=self.language,
                sample_rate=self.sample_rate
            )
            
            # Clean up
            os.unlink(temp_path)
            
            # Parse result
            recognized_text = result if isinstance(result, str) else str(result)
            confidence = 0.95  # PaddleSpeech doesn't return confidence
            
            logger.info(f"ASR result: {recognized_text}")
            return recognized_text, confidence
            
        except Exception as e:
            logger.error(f"PaddleSpeech recognition failed: {str(e)}")
            raise

class BaiduASR(ASRBase):
    """Baidu Cloud ASR implementation."""
    
    def __init__(self, api_key: str, secret_key: str, language: str = "zh_CN"):
        """Initialize Baidu ASR.
        
        Args:
            api_key: Baidu API Key
            secret_key: Baidu Secret Key
            language: Language code
        """
        super().__init__(api_key=api_key, language=language)
        self.secret_key = secret_key
        self.token = None
        self._refresh_token()
    
    def _refresh_token(self):
        """Refresh Baidu API token."""
        try:
            import requests
            auth_url = "https://openapi.baidu.com/oauth/2.0/token"
            params = {
                'grant_type': 'client_credentials',
                'client_id': self.api_key,
                'client_secret': self.secret_key
            }
            response = requests.post(auth_url, params=params, timeout=10)
            self.token = response.json().get('access_token')
            logger.info("Baidu token refreshed")
        except Exception as e:
            logger.error(f"Failed to refresh Baidu token: {str(e)}")
    
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Recognize speech using Baidu API.
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Tuple of (recognized_text, confidence_score)
        """
        if not self._validate_audio(audio_data):
            raise ValueError("Invalid audio data")
        
        if not self.token:
            raise RuntimeError("Baidu token not available")
        
        try:
            import requests
            asr_url = "https://vop.baidu.com/server_api"
            
            headers = {'Content-Type': 'audio/wav'}
            params = {
                'access_token': self.token,
                'format': 'wav',
                'rate': self.sample_rate,
                'dev_pid': 1536,  # Mandarin Chinese
                'speech_length': len(audio_data)
            }
            
            response = requests.post(
                asr_url,
                params=params,
                headers=headers,
                data=audio_data,
                timeout=Config.ASR_TIMEOUT
            )
            
            result_json = response.json()
            
            if result_json.get('err_no') == 0:
                recognized_text = result_json.get('result', [''])[0]
                confidence = result_json.get('result_detail', [{}])[0].get('confidence', 0.9)
                logger.info(f"Baidu ASR result: {recognized_text}")
                return recognized_text, confidence
            else:
                error_msg = result_json.get('err_msg', 'Unknown error')
                raise Exception(f"Baidu API error: {error_msg}")
                
        except Exception as e:
            logger.error(f"Baidu ASR failed: {str(e)}")
            raise

class ASREngine:
    """ASR Engine factory and manager."""
    
    def __init__(self, service: Optional[str] = None):
        """Initialize ASR Engine.
        
        Args:
            service: ASR service name ('paddlespeech', 'baidu', 'iflytek', 'google')
        """
        self.service_name = (service or Config.ASR_SERVICE).lower()
        self.engine = self._create_engine()
    
    def _create_engine(self) -> ASRBase:
        """Create appropriate ASR engine.
        
        Returns:
            ASRBase: Configured ASR engine instance
        """
        if self.service_name == "paddlespeech":
            logger.info("Using PaddleSpeech ASR")
            return PaddleSpeechASR(language=Config.ASR_LANGUAGE)
        
        elif self.service_name == "baidu":
            logger.info("Using Baidu Cloud ASR")
            api_key = Config.ASR_API_KEY
            secret_key = os.getenv("BAIDU_SECRET_KEY", "")
            if not api_key or not secret_key:
                raise ValueError("Baidu API key and secret key required")
            return BaiduASR(api_key=api_key, secret_key=secret_key, language=Config.ASR_LANGUAGE)
        
        else:
            logger.warning(f"Unsupported ASR service: {self.service_name}, falling back to PaddleSpeech")
            return PaddleSpeechASR(language=Config.ASR_LANGUAGE)
    
    def recognize(self, audio_data: bytes, language: Optional[str] = None) -> Tuple[str, float]:
        """Recognize speech from audio data.
        
        Args:
            audio_data: Raw audio bytes
            language: Optional language code override
            
        Returns:
            Tuple of (recognized_text, confidence_score)
            
        Raises:
            Exception: If recognition fails
        """
        if language and hasattr(self.engine, 'language'):
            self.engine.language = language
        
        return self.engine.recognize(audio_data)
