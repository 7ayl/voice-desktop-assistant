"""Automatic Speech Recognition (ASR) Engine Module."""

import os
import base64
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from .logger import setup_logger
from config.config import Config

logger = setup_logger(__name__)

class ASRBase(ABC):
    def __init__(self, api_key: Optional[str] = None, language: str = "zh_CN"):
        self.api_key = api_key
        self.language = language
        self.sample_rate = Config.AUDIO_SAMPLE_RATE

    @abstractmethod
    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        pass

    def _validate_audio(self, audio_data: bytes) -> bool:
        if not audio_data or len(audio_data) < 100:
            logger.warning("Audio data too short")
            return False
        return True

class PaddleSpeechASR(ASRBase):
    def __init__(self, language: str = "zh_CN"):
        super().__init__(api_key=None, language=language)
        try:
            from paddlespeech.cli.asr import ASRExecutor
            self.executor = ASRExecutor()
            logger.info("PaddleSpeech ASR engine initialized")
        except ImportError:
            logger.error("PaddleSpeech not installed")
            self.executor = None

    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        if not self._validate_audio(audio_data):
            raise ValueError("Invalid audio data")
        if self.executor is None:
            raise RuntimeError("PaddleSpeech engine not available")
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            result = self.executor(audio_file=temp_path, lang=self.language, sample_rate=self.sample_rate)
            os.unlink(temp_path)
            recognized_text = result if isinstance(result, str) else str(result)
            confidence = 0.95
            return recognized_text, confidence
        except Exception as e:
            logger.error(f"PaddleSpeech recognition failed: {str(e)}")
            raise

class BaiduASR(ASRBase):
    def __init__(self, api_key: str, secret_key: str, language: str = "zh_CN"):
        super().__init__(api_key=api_key, language=language)
        self.secret_key = secret_key
        self.token = None
        self._refresh_token()

    def _refresh_token(self):
        try:
            import requests
            url = "https://aip.baidubce.com/oauth/2.0/token"
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.api_key,
                'client_secret': self.secret_key
            }
            response = requests.post(url, headers=headers, data=data, timeout=10)
            result = response.json()
            if 'access_token' in result:
                self.token = result['access_token']
                logger.info("Baidu token refreshed successfully")
            else:
                error = result.get('error_description', result.get('error', 'Unknown error'))
                logger.error(f"Failed to get Baidu token: {error}")
                self.token = None
        except Exception as e:
            logger.error(f"Failed to refresh Baidu token: {str(e)}")
            self.token = None

    def recognize(self, audio_data: bytes) -> Tuple[str, float]:
        """Recognize speech using Baidu API (JSON方式)."""
        if not self._validate_audio(audio_data):
            raise ValueError("Invalid audio data")
        if not self.token:
            raise RuntimeError("Baidu token not available")
        try:
            import requests
            speech_base64 = base64.b64encode(audio_data).decode('utf-8')
            audio_len = len(audio_data)

            payload = {
                "format": "wav",
                "rate": self.sample_rate,
                "channel": 1,
                "cuid": "voice-desktop-assistant",
                "token": self.token,
                "speech": speech_base64,
                "len": audio_len,
                "dev_pid": 1537,
            }
            headers = {'Content-Type': 'application/json'}

            response = requests.post(
                "https://vop.baidu.com/server_api",
                headers=headers,
                json=payload,
                timeout=Config.ASR_TIMEOUT
            )
            result_json = response.json()
            logger.info(f"Baidu ASR response: {result_json}")

            if result_json.get('err_no') == 0:
                recognized_text = result_json.get('result', [''])[0]
                confidence = result_json.get('result_detail', [{}])[0].get('confidence', 0.9)
                return recognized_text, confidence
            else:
                error_msg = result_json.get('err_msg', 'Unknown error')
                err_no = result_json.get('err_no')
                raise Exception(f"Baidu API error: {error_msg} (err_no={err_no})")
        except Exception as e:
            logger.error(f"Baidu ASR failed: {str(e)}")
            raise

class ASREngine:
    def __init__(self, service: Optional[str] = None):
        self.service_name = (service or Config.ASR_SERVICE).lower()
        self.engine = self._create_engine()

    def _create_engine(self) -> ASRBase:
        if self.service_name == "paddlespeech":
            logger.info("Using PaddleSpeech ASR")
            return PaddleSpeechASR(language=Config.ASR_LANGUAGE)
        elif self.service_name == "baidu":
            logger.info("Using Baidu Cloud ASR")
            api_key = Config.ASR_API_KEY
            secret_key = Config.BAIDU_SECRET_KEY
            if not api_key or not secret_key:
                raise ValueError("Baidu API key and secret key required")
            return BaiduASR(api_key=api_key, secret_key=secret_key, language=Config.ASR_LANGUAGE)
        else:
            logger.warning(f"Unsupported ASR service: {self.service_name}, falling back to PaddleSpeech")
            return PaddleSpeechASR(language=Config.ASR_LANGUAGE)

    def recognize(self, audio_data: bytes, language: Optional[str] = None) -> Tuple[str, float]:
        if language and hasattr(self.engine, 'language'):
            self.engine.language = language
        return self.engine.recognize(audio_data)