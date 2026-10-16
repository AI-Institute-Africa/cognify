"""Chat shim routing all text generation through the OpenAI provider."""
import logging
from typing import Optional, List, Dict, Any, Tuple
from services.ai_provider import ai_provider, scrub_banned_words

logger = logging.getLogger(__name__)

class UserMessage:
    def __init__(self, text: str = "", image_url: Optional[str] = None):
        self.text = text
        self.content = text
        self.image_url = image_url

    def __str__(self):
        return self.text

class SystemMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.content = text

    def __str__(self):
        return self.text

class ChatResponse(str):
    def __new__(cls, text: str = ""):
        return super().__new__(cls, str(text))

    def __init__(self, text: str = ""):
        self.text = str(text)
        self.content = str(text)

    def __str__(self):
        return self.text

class LlmChat:
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None, system_message: Optional[str] = None):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message or "You are a professional educational advisor for Cognify."
        self.provider = "openai"
        self.model = "gpt-4o-mini"
        self.messages_history: List[Dict[str, str]] = []

    def with_model(self, provider: str, model: str):
        self.provider = provider
        self.model = model
        return self

    def with_params(self, **kwargs):
        return self

    async def send_message(self, message: Any) -> ChatResponse:
        user_text = message.text if hasattr(message, "text") else str(message)
        self.messages_history.append({"role": "user", "content": user_text})
        
        reply = await ai_provider.chat_completion(
            messages=self.messages_history,
            system_prompt=self.system_message
        )
        scrubbed = scrub_banned_words(reply)
        self.messages_history.append({"role": "assistant", "content": scrubbed})
        return ChatResponse(scrubbed)

    async def send_message_multimodal_response(self, message: Any) -> Tuple[str, List[Dict[str, Any]]]:
        user_text = message.text if hasattr(message, "text") else str(message)
        from services.advanced_ai import generate_educational_visual
        
        vis_svg, _ = await generate_educational_visual(concept=user_text[:40])
        text_resp = await self.send_message(message)
        
        images = []
        if vis_svg and vis_svg.startswith("data:"):
            parts = vis_svg.split(",", 1)
            mime = parts[0].split(";")[0].replace("data:", "")
            data = parts[1] if len(parts) > 1 else ""
            images.append({"data": data, "mime_type": mime})
            
        return str(text_resp), images

class Chat:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5.2"):
        self.api_key = api_key
        self.model = model
        self.system_prompt: Optional[str] = None
        self.messages: List[Dict[str, str]] = []

    async def send_message(self, message: Any) -> str:
        if isinstance(message, SystemMessage):
            self.system_prompt = message.text
            return ""
        
        user_text = message.text if hasattr(message, "text") else str(message)
        self.messages.append({"role": "user", "content": user_text})
        
        reply = await ai_provider.chat_completion(
            messages=self.messages,
            system_prompt=self.system_prompt
        )
        return scrub_banned_words(reply)
