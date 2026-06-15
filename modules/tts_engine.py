"""Text-to-Speech (TTS) Engine Module.

Supports multiple TTS services:
- Edge TTS (Microsoft, free, high-quality)
- Baidu Cloud TTS
- iFlytek TTS
- Google Cloud TTS
"""

import os
import io
from abc import ABC, abstractmethod
from typing import Optional
from .logger import setup_logger
from config.config import Config

logger = setup_logger(__name__)

class TTSBase(ABC):
    """Abstract base class for TTS engines."""
    
    def __init__(self, api_key: Optional[str] = None, language: str = "zh_CN", voice: str = None):
        """Initialize TTS engine.
        
        Args:
            api_key: API key for cloud-based services
            language: Language code (e.g., 'zh_CN', 'en_US')
            voice: Specific voice/speaker to use
        """
        self.api_key = api_key
        self.language = language
        self.voice = voice
        self.sample_rate = Config.AUDIO_SAMPLE_RATE
    
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        """Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data in bytes (WAV format preferred)
            
        Raises:
            Exception: If synthesis fails
        """
        pass

class EdgeTTS(TTSBase):
    """Edge TTS implementation (Microsoft)."""
    
    def __init__(self, language: str = "zh-CN", voice: str = None):
        """Initialize Edge TTS.
        
        Args:
            language: Language code (e.g., 'zh-CN', 'en-US')
            voice: Voice name (e.g., 'zh-CN-XiaoxiaoNeural')
        """
        super().__init__(api_key=None, language=language, voice=voice)
        self.voice = voice or Config.TTS_VOICE
        
        try:
            import edge_tts
            self.communicate = edge_tts.Communicate
            logger.info("Edge TTS engine initialized")
        except ImportError:
            logger.error("edge_tts not installed. Install with: pip install edge-tts")
            self.communicate = None

    def synthesize(self, text: str) -> bytes:
        """Synthesize text using Edge TTS (new API)."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        if self.communicate is None:
            raise RuntimeError("Edge TTS engine not available")
        try:
            import asyncio

            async def _synthesize():
                audio_data = io.BytesIO()
                communicate = self.communicate(
                    text,
                    voice=self.voice,
                    rate="+0%"
                )
                # 新版 edge-tts 使用 stream() 而不是 stream_by_chunk
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data.write(chunk["data"])
                return audio_data.getvalue()

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(_synthesize())
            loop.close()
            logger.info(f"TTS synthesis completed, audio size: {len(audio_bytes)} bytes")
            return audio_bytes
        except Exception as e:
            logger.error(f"Edge TTS synthesis failed: {str(e)}")
            raise

class BaiduTTS(TTSBase):
    """Baidu Cloud TTS implementation."""
    
    def __init__(self, api_key: str, secret_key: str, language: str = "zh_CN", voice: str = None):
        """Initialize Baidu TTS.
        
        Args:
            api_key: Baidu API Key
            secret_key: Baidu Secret Key
            language: Language code
            voice: Voice/speaker ID
        """
        super().__init__(api_key=api_key, language=language, voice=voice)
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
            logger.info("Baidu token refreshed for TTS")
        except Exception as e:
            logger.error(f"Failed to refresh Baidu TTS token: {str(e)}")
    
    def synthesize(self, text: str) -> bytes:
        """Synthesize text using Baidu API.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data in bytes (PCM format)
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if not self.token:
            raise RuntimeError("Baidu token not available")
        
        try:
            import requests
            tts_url = "https://tsn.baidu.com/text2audio"
            
            params = {
                'access_token': self.token,
                'tex': text,
                'per': self.voice or '0',  # Speaker ID
                'aue': 'wav',
                'spd': '5',  # Speaking speed
                'pit': '5',  # Pitch
                'vol': '9',  # Volume
            }
            
            response = requests.post(
                tts_url,
                params=params,
                timeout=Config.TTS_TIMEOUT
            )
            
            # Check if response is audio data
            if response.headers.get('Content-Type', '').startswith('audio'):
                logger.info(f"Baidu TTS synthesis completed, audio size: {len(response.content)} bytes")
                return response.content
            else:
                error_data = response.json()
                raise Exception(f"Baidu TTS error: {error_data.get('err_msg', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Baidu TTS synthesis failed: {str(e)}")
            raise

class TTSEngine:
    """TTS Engine factory and manager."""
    
    def __init__(self, service: Optional[str] = None):
        """Initialize TTS Engine.
        
        Args:
            service: TTS service name ('edge-tts', 'baidu', 'iflytek', 'google')
        """
        self.service_name = (service or Config.TTS_SERVICE).lower()
        self.engine = self._create_engine()
    
    def _create_engine(self) -> TTSBase:
        """Create appropriate TTS engine.
        
        Returns:
            TTSBase: Configured TTS engine instance
        """
        if self.service_name == "edge-tts":
            logger.info("Using Edge TTS")
            return EdgeTTS(language=Config.TTS_LANGUAGE, voice=Config.TTS_VOICE)
        
        elif self.service_name == "baidu":
            logger.info("Using Baidu Cloud TTS")
            api_key = Config.TTS_API_KEY
            secret_key = os.getenv("BAIDU_SECRET_KEY", "")
            if not api_key or not secret_key:
                raise ValueError("Baidu API key and secret key required")
            return BaiduTTS(api_key=api_key, secret_key=secret_key, language=Config.TTS_LANGUAGE)
        
        else:
            logger.warning(f"Unsupported TTS service: {self.service_name}, falling back to Edge TTS")
            return EdgeTTS(language=Config.TTS_LANGUAGE, voice=Config.TTS_VOICE)
    
    def synthesize(self, text: str) -> bytes:
        """Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data in bytes
            
        Raises:
            Exception: If synthesis fails
        """
        return self.engine.synthesize(text)
