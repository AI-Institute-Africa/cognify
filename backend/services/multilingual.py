"""
Multilingual Support Service for EduOS 2026
Supports African languages: Shona, Ndebele, Zulu, Swahili, Xhosa, and more
"""
import os
import logging
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Supported languages with metadata
SUPPORTED_LANGUAGES = {
    # African Languages
    "sn": {"name": "Shona", "native": "chiShona", "region": "Zimbabwe"},
    "nd": {"name": "Ndebele", "native": "isiNdebele", "region": "Zimbabwe/South Africa"},
    "zu": {"name": "Zulu", "native": "isiZulu", "region": "South Africa"},
    "sw": {"name": "Swahili", "native": "Kiswahili", "region": "East Africa"},
    "xh": {"name": "Xhosa", "native": "isiXhosa", "region": "South Africa"},
    "st": {"name": "Sesotho", "native": "Sesotho", "region": "South Africa/Lesotho"},
    "tn": {"name": "Setswana", "native": "Setswana", "region": "Botswana/South Africa"},
    "af": {"name": "Afrikaans", "native": "Afrikaans", "region": "South Africa"},
    "yo": {"name": "Yoruba", "native": "Yorùbá", "region": "Nigeria"},
    "ig": {"name": "Igbo", "native": "Igbo", "region": "Nigeria"},
    "ha": {"name": "Hausa", "native": "Hausa", "region": "Nigeria/Niger"},
    "am": {"name": "Amharic", "native": "አማርኛ", "region": "Ethiopia"},
    "om": {"name": "Oromo", "native": "Afaan Oromoo", "region": "Ethiopia"},
    "so": {"name": "Somali", "native": "Soomaali", "region": "Somalia"},
    "rw": {"name": "Kinyarwanda", "native": "Ikinyarwanda", "region": "Rwanda"},
    "lg": {"name": "Luganda", "native": "Oluganda", "region": "Uganda"},
    "ny": {"name": "Chichewa", "native": "Chichewa", "region": "Malawi"},
    # Global Languages
    "en": {"name": "English", "native": "English", "region": "Global"},
    "fr": {"name": "French", "native": "Français", "region": "Global/Africa"},
    "pt": {"name": "Portuguese", "native": "Português", "region": "Global/Africa"},
    "ar": {"name": "Arabic", "native": "العربية", "region": "North Africa/Middle East"},
    "es": {"name": "Spanish", "native": "Español", "region": "Global"},
    "zh": {"name": "Chinese", "native": "中文", "region": "Global"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "region": "India"},
}

# UI Translation keys (English as base)
UI_TRANSLATIONS = {
    "en": {
        # Navigation
        "nav.dashboard": "Dashboard",
        "nav.courses": "Courses",
        "nav.grades": "Grades",
        "nav.attendance": "Attendance",
        "nav.fees": "Fees",
        "nav.achievements": "Achievements",
        "nav.ai_mentor": "AI Mentor",
        "nav.knowledge_graph": "Knowledge Graph",
        "nav.learn_by_teaching": "Learn by Teaching",
        "nav.learning_journey": "Learning Journey",
        "nav.study_groups": "Study Groups",
        "nav.virtual_classroom": "Virtual Classroom",
        "nav.settings": "Settings",
        "nav.logout": "Logout",
        
        # Common Actions
        "action.save": "Save",
        "action.cancel": "Cancel",
        "action.submit": "Submit",
        "action.delete": "Delete",
        "action.edit": "Edit",
        "action.search": "Search",
        "action.filter": "Filter",
        "action.create": "Create",
        "action.upload": "Upload",
        "action.download": "Download",
        "action.share": "Share",
        "action.enroll": "Enroll",
        "action.start": "Start",
        "action.continue": "Continue",
        "action.complete": "Complete",
        
        # AI Features
        "ai.hint": "Get Hint",
        "ai.analogy": "Show Analogy",
        "ai.ask_question": "Ask AI",
        "ai.generate": "Generate",
        "ai.translate": "Translate",
        "ai.speak": "Listen",
        "ai.teach_back": "Teach It Back",
        "ai.create_question": "Create Question",
        "ai.analyze": "Analyze",
        
        # Learning
        "learning.concept": "Concept",
        "learning.lesson": "Lesson",
        "learning.quiz": "Quiz",
        "learning.assignment": "Assignment",
        "learning.progress": "Progress",
        "learning.mastery": "Mastery",
        "learning.review": "Review",
        "learning.practice": "Practice",
        
        # Messages
        "msg.welcome": "Welcome",
        "msg.success": "Success",
        "msg.error": "Error",
        "msg.loading": "Loading...",
        "msg.no_data": "No data available",
        "msg.confirm_delete": "Are you sure you want to delete?",
        
        # Multimodal
        "content.video": "Video",
        "content.audio": "Audio",
        "content.image": "Image",
        "content.text": "Text",
        "content.interactive": "Interactive",
        
        # Avatar/Tutor
        "tutor.select": "Select Your Tutor",
        "tutor.clone": "Clone Voice",
        "tutor.change": "Change Avatar",
        "tutor.speak": "Speak to Me",
    },
    "sw": {
        # Navigation - Swahili
        "nav.dashboard": "Dashibodi",
        "nav.courses": "Kozi",
        "nav.grades": "Daraja",
        "nav.attendance": "Mahudhurio",
        "nav.fees": "Ada",
        "nav.achievements": "Mafanikio",
        "nav.ai_mentor": "Mshauri wa AI",
        "nav.knowledge_graph": "Grafu ya Maarifa",
        "nav.learn_by_teaching": "Jifunze kwa Kufundisha",
        "nav.learning_journey": "Safari ya Kujifunza",
        "nav.study_groups": "Vikundi vya Kusoma",
        "nav.virtual_classroom": "Darasa Pepe",
        "nav.settings": "Mipangilio",
        "nav.logout": "Ondoka",
        
        # Common Actions
        "action.save": "Hifadhi",
        "action.cancel": "Ghairi",
        "action.submit": "Wasilisha",
        "action.search": "Tafuta",
        "action.enroll": "Jiandikishe",
        "action.start": "Anza",
        "action.continue": "Endelea",
        
        # AI Features
        "ai.hint": "Pata Dokezo",
        "ai.ask_question": "Uliza AI",
        "ai.translate": "Tafsiri",
        "ai.speak": "Sikiliza",
        
        # Messages
        "msg.welcome": "Karibu",
        "msg.success": "Imefanikiwa",
        "msg.error": "Hitilafu",
        "msg.loading": "Inapakia...",
    },
    "zu": {
        # Navigation - Zulu
        "nav.dashboard": "Ibhodi",
        "nav.courses": "Izifundo",
        "nav.grades": "Amabanga",
        "nav.attendance": "Ukuza",
        "nav.fees": "Imali",
        "nav.achievements": "Imiphumela",
        "nav.ai_mentor": "Umeluleki we-AI",
        "nav.settings": "Izilungiselelo",
        "nav.logout": "Phuma",
        
        # Common Actions
        "action.save": "Gcina",
        "action.cancel": "Khansela",
        "action.submit": "Thumela",
        "action.search": "Sesha",
        
        # Messages
        "msg.welcome": "Wamkelekile",
        "msg.success": "Kuphumelele",
        "msg.error": "Iphutha",
    },
    "sn": {
        # Navigation - Shona
        "nav.dashboard": "Bhodhi",
        "nav.courses": "Zvidzidzo",
        "nav.grades": "Magredi",
        "nav.attendance": "Kupinda",
        "nav.fees": "Mari",
        "nav.achievements": "Zvakawanikwa",
        "nav.ai_mentor": "Mudzidzisi weAI",
        "nav.settings": "Zvigadziriso",
        "nav.logout": "Buda",
        
        # Messages
        "msg.welcome": "Titambire",
        "msg.success": "Zvabudirira",
        "msg.error": "Kukanganisa",
    },
    "nd": {
        # Navigation - Ndebele
        "nav.dashboard": "Ibhodi",
        "nav.courses": "Izifundo",
        "nav.settings": "Izilungiselelo",
        "nav.logout": "Phuma",
        
        "msg.welcome": "Siyakwamukela",
    },
    "xh": {
        # Navigation - Xhosa
        "nav.dashboard": "Ibhodi",
        "nav.courses": "Izifundo",
        "nav.settings": "Iisetingi",
        "nav.logout": "Phuma",
        
        "msg.welcome": "Wamkelekile",
    },
}

def get_supported_languages() -> list:
    """Get list of all supported languages with metadata."""
    return [
        {
            "code": code,
            **meta
        }
        for code, meta in SUPPORTED_LANGUAGES.items()
    ]

def get_ui_translation(key: str, language: str = "en") -> str:
    """Get UI translation for a key in specified language."""
    translations = UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["en"])
    return translations.get(key, UI_TRANSLATIONS["en"].get(key, key))

def get_all_translations(language: str = "en") -> Dict[str, str]:
    """Get all UI translations for a language."""
    base = UI_TRANSLATIONS["en"].copy()
    if language != "en" and language in UI_TRANSLATIONS:
        base.update(UI_TRANSLATIONS[language])
    return base


async def translate_text(
    text: str,
    target_language: str,
    source_language: str = "en"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Translate text to target language using AI.
    Returns (translated_text, error_message)
    """
    if target_language == source_language:
        return text, None
    
    target_info = SUPPORTED_LANGUAGES.get(target_language, {"name": target_language})
    source_info = SUPPORTED_LANGUAGES.get(source_language, {"name": source_language})
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"translate-{target_language}",
            system_message=f"""You are an expert translator specializing in African languages.
            Translate the following text from {source_info['name']} to {target_info['name']}.
            Preserve the meaning, tone, and cultural context.
            Only output the translation, nothing else."""
        )
        
        response = await chat.send_message(UserMessage(text=text))
        return response, None
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return None, str(e)


async def translate_content_batch(
    contents: list,
    target_language: str,
    source_language: str = "en"
) -> list:
    """
    Translate multiple content items in batch.
    """
    results = []
    for content in contents:
        translated, error = await translate_text(content, target_language, source_language)
        results.append({
            "original": content,
            "translated": translated,
            "error": error
        })
    return results


async def detect_language(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect the language of given text.
    Returns (language_code, error_message)
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        languages_list = ", ".join([f"{code}: {info['name']}" for code, info in SUPPORTED_LANGUAGES.items()])
        
        chat = LlmChat(
            api_key=api_key,
            session_id="detect-language",
            system_message=f"""Detect the language of the text. 
            Supported languages: {languages_list}
            Respond with ONLY the language code (e.g., 'en', 'sw', 'zu', etc.)."""
        )
        
        response = await chat.send_message(UserMessage(text=f"Detect language: {text[:500]}"))
        
        # Clean response to get language code
        code = response.strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code, None
        return "en", None  # Default to English
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        return None, str(e)
