"""Services package"""
from .ai_service import (
    get_emergent_llm_response,
    generate_elevenlabs_audio,
    get_zoom_access_token
)

from .advanced_ai import (
    generate_tts_audio,
    generate_avatar_image,
    generate_educational_visual,
    get_ai_response,
    generate_micro_hint,
    generate_analogy,
    generate_comprehension_questions,
    analyze_syllabus_content,
    generate_interactive_lesson,
    simulate_student_interaction,
    evaluate_teaching_quality,
    analyze_user_question,
    evaluate_user_answer,
    generate_assignment,
    evaluate_assignment_submission,
    generate_multidisciplinary_lesson,
    analyze_learner_identity,
    personalize_content_for_identity,
    decompose_outcome
)

from .multilingual import (
    SUPPORTED_LANGUAGES,
    UI_TRANSLATIONS,
    get_supported_languages,
    get_ui_translation,
    get_all_translations,
    translate_text,
    translate_content_batch,
    detect_language
)

__all__ = [
    # AI Service
    'get_emergent_llm_response',
    'generate_elevenlabs_audio',
    'get_zoom_access_token',
    # Advanced AI
    'generate_tts_audio',
    'generate_avatar_image',
    'generate_educational_visual',
    'get_ai_response',
    'generate_micro_hint',
    'generate_analogy',
    'generate_comprehension_questions',
    'analyze_syllabus_content',
    'generate_interactive_lesson',
    'simulate_student_interaction',
    'evaluate_teaching_quality',
    'analyze_user_question',
    'evaluate_user_answer',
    'generate_assignment',
    'evaluate_assignment_submission',
    'generate_multidisciplinary_lesson',
    'analyze_learner_identity',
    'personalize_content_for_identity',
    'decompose_outcome',
    # Multilingual
    'SUPPORTED_LANGUAGES',
    'UI_TRANSLATIONS',
    'get_supported_languages',
    'get_ui_translation',
    'get_all_translations',
    'translate_text',
    'translate_content_batch',
    'detect_language',
]
