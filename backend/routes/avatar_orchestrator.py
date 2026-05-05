"""
Avatar Learning Orchestrator - HeyGen Integration
Handles: Script generation, HeyGen video creation, interactive tutor Q&A,
multi-language dubbing, assessment generation, adaptive difficulty
"""
import os
import logging
import uuid
import json
import asyncio
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Body, Request
from database import db
from auth_utils import get_current_user, serialize_doc

logger = logging.getLogger(__name__)

avatar_router = APIRouter(prefix="/avatar-orchestrator", tags=["Avatar Orchestrator"])

HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY', '')
HEYGEN_BASE = "https://api.heygen.com"

# Default avatars for teaching
DEFAULT_AVATARS = [
    {"id": "Angela-inTshirt-20220820", "name": "Angela", "style": "normal"},
    {"id": "josh_lite3_20230714", "name": "Josh", "style": "normal"},
    {"id": "Kayla-incasualsuit-20220818", "name": "Kayla", "style": "normal"},
    {"id": "Abigail_expressive_2024112501", "name": "Abigail", "style": "normal"},
]


async def generate_teaching_script(lesson_content: str, lesson_title: str, user_level: str, language: str = "en") -> str:
    """Convert lesson content into a natural teaching narration script"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import litellm
        litellm.num_retries = 0
        litellm.request_timeout = 50

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return lesson_content

        level_guide = {
            "beginner": "Use simple language, explain every concept from scratch, use analogies and real-world examples.",
            "intermediate": "Assume basic knowledge, focus on connections and deeper understanding.",
            "advanced": "Be technical, focus on nuances, edge cases, and advanced applications."
        }

        system_msg = f"""You are an engaging educator creating a spoken teaching script.
Convert the lesson content into natural spoken narration.
Rules:
- Write as if speaking directly to the student
- NO bullet points, NO headings, NO markdown
- Use conversational transitions: "Now let's look at...", "Here's something interesting..."
- Adapt to {user_level} level: {level_guide.get(user_level, level_guide['intermediate'])}
- Keep it under 800 words for a ~5 minute video
- Language: {language}
- Make it engaging, clear, and educational"""

        chat = LlmChat(api_key=api_key, session_id=f"script-{uuid.uuid4()}", system_message=system_msg)
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=f"Create a teaching script for: {lesson_title}\n\nContent:\n{lesson_content[:6000]}")),
            timeout=50
        )
        return (response.text if hasattr(response, 'text') else str(response)).strip()
    except Exception as e:
        logger.error(f"Script generation failed: {e}")
        return lesson_content[:2000]


@avatar_router.get("/avatars")
async def get_available_avatars(current_user: dict = Depends(get_current_user)):
    """Get list of available HeyGen avatars"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{HEYGEN_BASE}/v2/avatars", headers={"X-Api-Key": HEYGEN_API_KEY})
            data = resp.json()
            avatars = data.get('data', {}).get('avatars', [])
            # Return first 20 useful avatars
            result = []
            for a in avatars[:50]:
                result.append({
                    "avatar_id": a.get("avatar_id"),
                    "avatar_name": a.get("avatar_name"),
                    "preview_url": a.get("preview_image_url") or a.get("preview_video_url"),
                })
            return {"avatars": result, "total": len(result)}
    except Exception as e:
        logger.error(f"Failed to fetch avatars: {e}")
        return {"avatars": DEFAULT_AVATARS, "total": len(DEFAULT_AVATARS)}


@avatar_router.get("/voices")
async def get_available_voices(current_user: dict = Depends(get_current_user)):
    """Get list of available HeyGen voices"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{HEYGEN_BASE}/v2/voices", headers={"X-Api-Key": HEYGEN_API_KEY})
            data = resp.json()
            voices = data.get('data', {}).get('voices', [])
            result = []
            for v in voices[:100]:
                if v.get('language', '').startswith('en') or v.get('display_name'):
                    result.append({
                        "voice_id": v.get("voice_id"),
                        "name": v.get("display_name") or v.get("name", "Unknown"),
                        "language": v.get("language", "en"),
                        "gender": v.get("gender", "unknown"),
                    })
            return {"voices": result, "total": len(result)}
    except Exception as e:
        logger.error(f"Failed to fetch voices: {e}")
        return {"voices": [], "total": 0}


@avatar_router.post("/generate-video")
async def generate_avatar_video(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Full pipeline: Generate teaching script and create HeyGen avatar video"""
    body = await request.json()
    lesson_id = body.get("lesson_id")
    course_id = body.get("course_id")
    lesson_content = body.get("lesson_content", "")
    lesson_title = body.get("lesson_title", "Lesson")
    avatar_id = body.get("avatar_id", DEFAULT_AVATARS[0]["id"])
    voice_id = body.get("voice_id")
    user_level = body.get("user_level", "intermediate")
    language = body.get("language", "en")
    background = body.get("background", {"type": "color", "value": "#1a1a2e"})

    # If no content provided, fetch from lesson/course
    if not lesson_content:
        if lesson_id:
            lesson = await db.lessons.find_one({"id": lesson_id}, {"_id": 0})
            if lesson:
                lesson_content = lesson.get("content", "")
                lesson_title = lesson.get("title", lesson_title)
        elif course_id:
            contents = await db.course_contents.find({"course_id": course_id}, {"_id": 0}).to_list(5)
            if contents:
                lesson_content = contents[0].get("text", "")
                lesson_title = contents[0].get("title", lesson_title)

    if not lesson_content:
        raise HTTPException(status_code=400, detail="No lesson content available")

    # Step 1: Generate teaching script
    script = await generate_teaching_script(lesson_content, lesson_title, user_level, language)

    # Step 2: Resolve voice
    if not voice_id:
        voice_id = "1bd001e7e50f421d891986aad5158bc8"  # Default HeyGen voice

    # Step 3: Create HeyGen video
    payload = {
        "video_inputs": [{
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal"
            },
            "voice": {
                "type": "text",
                "input_text": script[:5000],
                "voice_id": voice_id,
                "speed": 1.0
            },
            "background": background
        }],
        "dimension": {"width": 1280, "height": 720}
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{HEYGEN_BASE}/v2/video/generate",
                headers={"X-Api-Key": HEYGEN_API_KEY, "Content-Type": "application/json"},
                json=payload
            )
            result = resp.json()

        video_id = result.get("data", {}).get("video_id")
        if not video_id:
            raise HTTPException(status_code=500, detail=f"HeyGen error: {result.get('message', 'Unknown error')}")

        # Store video record
        video_record = {
            "id": str(uuid.uuid4()),
            "heygen_video_id": video_id,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "lesson_title": lesson_title,
            "avatar_id": avatar_id,
            "voice_id": voice_id,
            "user_level": user_level,
            "language": language,
            "script": script,
            "status": "processing",
            "created_by": current_user['id'],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.avatar_videos.insert_one(video_record)
        video_record.pop('_id', None)

        return {
            "message": "Avatar video generation started",
            "video_id": video_id,
            "record_id": video_record['id'],
            "status": "processing",
            "script_preview": script[:300]
        }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HeyGen API error: {str(e)}")


@avatar_router.get("/video-status/{video_id}")
async def check_video_status(video_id: str, current_user: dict = Depends(get_current_user)):
    """Check HeyGen video generation status"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{HEYGEN_BASE}/v1/video_status.get?video_id={video_id}",
                headers={"X-Api-Key": HEYGEN_API_KEY}
            )
            data = resp.json().get("data", {})

        status = data.get("status", "unknown")
        video_url = data.get("video_url")

        # Update DB record
        if video_url:
            await db.avatar_videos.update_one(
                {"heygen_video_id": video_id},
                {"$set": {"status": "completed", "video_url": video_url}}
            )

        return {
            "video_id": video_id,
            "status": status,
            "video_url": video_url,
            "thumbnail_url": data.get("thumbnail_url"),
            "duration": data.get("duration")
        }
    except Exception as e:
        return {"video_id": video_id, "status": "error", "error": str(e)}


@avatar_router.post("/interactive-tutor")
async def interactive_tutor_qa(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Interactive Q&A with avatar tutor based on lesson context"""
    body = await request.json()
    question = body.get("question", "")
    lesson_content = body.get("lesson_content", "")
    lesson_title = body.get("lesson_title", "")
    conversation_history = body.get("history", [])

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import litellm
        litellm.num_retries = 0
        litellm.request_timeout = 40

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI not configured")

        system_msg = f"""You are a friendly, knowledgeable teacher avatar.
You are teaching: {lesson_title}
Lesson context: {lesson_content[:3000]}

Rules:
- Stay in teacher persona
- Answer based on lesson content
- Be concise and clear (2-4 sentences max)
- End with a guiding follow-up question when appropriate
- If asked something outside the lesson, redirect politely"""

        chat = LlmChat(api_key=api_key, session_id=f"tutor-{current_user['id']}-{uuid.uuid4()}", system_message=system_msg)
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=question)),
            timeout=30
        )
        answer = (response.text if hasattr(response, 'text') else str(response)).strip()

        return {
            "mode": "interactive_tutor",
            "response": answer,
            "question": question
        }
    except Exception as e:
        logger.error(f"Tutor Q&A error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@avatar_router.post("/translate-script")
async def translate_teaching_script(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Translate teaching script to another language"""
    body = await request.json()
    script = body.get("script", "")
    target_language = body.get("target_language", "sw")
    source_language = body.get("source_language", "en")

    if not script:
        raise HTTPException(status_code=400, detail="Script is required")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get('EMERGENT_LLM_KEY')

        chat = LlmChat(api_key=api_key, session_id=f"translate-{uuid.uuid4()}",
                       system_message=f"Translate the following teaching script from {source_language} to {target_language}. Keep the teaching tone natural.")
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=script[:5000])),
            timeout=40
        )
        translated = (response.text if hasattr(response, 'text') else str(response)).strip()

        return {
            "mode": "multi_language",
            "original_language": source_language,
            "target_language": target_language,
            "translated_script": translated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@avatar_router.post("/generate-assessment")
async def generate_lesson_assessment(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate quiz/assessment from lesson content"""
    body = await request.json()
    lesson_content = body.get("lesson_content", "")
    lesson_title = body.get("lesson_title", "")
    question_count = body.get("question_count", 5)

    if not lesson_content:
        raise HTTPException(status_code=400, detail="Lesson content required")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get('EMERGENT_LLM_KEY')

        system_msg = f"""Generate a quiz from the lesson. Return ONLY valid JSON:
{{
  "questions": [
    {{"type": "multiple_choice", "question": "...", "options": ["A","B","C","D"], "answer": "A"}},
    {{"type": "short_answer", "question": "...", "answer": "..."}}
  ]
}}
Generate {question_count} questions. Mix multiple_choice and short_answer."""

        chat = LlmChat(api_key=api_key, session_id=f"quiz-{uuid.uuid4()}", system_message=system_msg)
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=f"Lesson: {lesson_title}\n\n{lesson_content[:5000]}")),
            timeout=40
        )
        text = (response.text if hasattr(response, 'text') else str(response)).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        assessment = json.loads(text)
        return {"mode": "assessment", **assessment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@avatar_router.post("/adaptive-rewrite")
async def adaptive_difficulty_rewrite(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Rewrite lesson content for a different difficulty level"""
    body = await request.json()
    content = body.get("content", "")
    target_level = body.get("target_level", "beginner")

    if not content:
        raise HTTPException(status_code=400, detail="Content required")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get('EMERGENT_LLM_KEY')

        level_desc = {
            "beginner": "simple language, real-world analogies, step-by-step explanations",
            "intermediate": "moderate depth, some technical terms with explanations",
            "advanced": "technical language, nuances, edge cases, academic depth"
        }

        chat = LlmChat(api_key=api_key, session_id=f"adapt-{uuid.uuid4()}",
                       system_message=f"Rewrite this educational content for {target_level} level: {level_desc.get(target_level, '')}. Keep it as a natural teaching script.")
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=content[:5000])),
            timeout=40
        )
        rewritten = (response.text if hasattr(response, 'text') else str(response)).strip()

        return {
            "mode": "adaptive_rewrite",
            "target_level": target_level,
            "updated_script": rewritten
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@avatar_router.post("/generate-slides")
async def generate_slides_from_lesson(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Generate slide content from lesson text"""
    body = await request.json()
    lesson_content = body.get("lesson_content", "")
    lesson_title = body.get("lesson_title", "Lesson")

    if not lesson_content:
        raise HTTPException(status_code=400, detail="Lesson content required")

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get('EMERGENT_LLM_KEY')

        system_msg = """Create presentation slides from lesson content. Return ONLY valid JSON array:
[
  {"slide_number": 1, "title": "Title Slide", "content": "subtitle text", "notes": "speaker notes"},
  {"slide_number": 2, "title": "Key Concept", "content": "3-5 bullet points", "notes": "explanation"}
]
Create 5-8 slides. Content should be concise bullet points. Notes should have detailed explanation."""

        chat = LlmChat(api_key=api_key, session_id=f"slides-{uuid.uuid4()}", system_message=system_msg)
        chat.with_model("openai", "gpt-5.2")

        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=f"Create slides for: {lesson_title}\n\n{lesson_content[:5000]}")),
            timeout=40
        )
        text = (response.text if hasattr(response, 'text') else str(response)).strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        slides = json.loads(text)
        return {"slides": slides, "total": len(slides), "lesson_title": lesson_title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
