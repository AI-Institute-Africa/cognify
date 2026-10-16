"""Compatibility shim preventing non-Higgsfield video generation."""
from typing import Optional

class OpenAIVideoGeneration:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def generate_video(self, prompt: str, **kwargs) -> str:
        raise RuntimeError("Video generation is only supported through the Higgsfield service")
