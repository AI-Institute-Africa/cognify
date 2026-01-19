"""AI and LLM services"""
import os
import logging
from typing import Optional

async def get_emergent_llm_response(messages: list, system_prompt: str = None) -> str:
    """Get response from Emergent LLM"""
    try:
        from emergentintegrations.llm.chat import Chat, UserMessage, SystemMessage
        
        chat = Chat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            model="gpt-5.2"
        )
        
        if system_prompt:
            await chat.send_message(SystemMessage(text=system_prompt))
        
        for msg in messages:
            if msg.get('role') == 'user':
                response = await chat.send_message(UserMessage(text=msg['content']))
        
        return response
    except Exception as e:
        logging.error(f"Emergent LLM error: {str(e)}")
        raise

async def generate_elevenlabs_audio(text: str, voice_id: str = None) -> Optional[str]:
    """Generate audio using ElevenLabs API"""
    try:
        import httpx
        import base64
        
        api_key = os.environ.get('ELEVENLABS_API_KEY')
        if not api_key:
            return None
        
        voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"  # Default voice
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text[:1000],  # Limit text length
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return f"data:audio/mpeg;base64,{audio_base64}"
        
        return None
    except Exception as e:
        logging.error(f"ElevenLabs error: {str(e)}")
        return None

async def get_zoom_access_token() -> Optional[str]:
    """Get Zoom OAuth access token"""
    try:
        import httpx
        import base64
        
        client_id = os.environ.get('ZOOM_CLIENT_ID')
        client_secret = os.environ.get('ZOOM_CLIENT_SECRET')
        account_id = os.environ.get('ZOOM_ACCOUNT_ID')
        
        if not all([client_id, client_secret, account_id]):
            return None
        
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://zoom.us/oauth/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "account_credentials",
                    "account_id": account_id
                }
            )
            
            if response.status_code == 200:
                return response.json().get('access_token')
        
        return None
    except Exception as e:
        logging.error(f"Zoom token error: {str(e)}")
        return None
