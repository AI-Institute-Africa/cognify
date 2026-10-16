"""OpenAI module shim"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OpenAITextToSpeech:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate_speech_base64(
        self,
        text: str,
        model: str = "tts-1",
        voice: str = "nova",
        speed: float = 1.0
    ) -> str:
        from services.ai_provider import AIProvider

        provider = AIProvider()
        if self.api_key:
            provider.openai_key = self.api_key
        return await provider.generate_audio(text=text, model=model, voice=voice, speed=speed)
