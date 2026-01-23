"""
Advanced AI Services for EduOS 2026
Includes: TTS, Image Generation, LLM Chat, Content Analysis
"""
import os
import base64
import logging
import json
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# =============================================================================
# TEXT-TO-SPEECH SERVICE (Using Emergent LLM Key)
# =============================================================================

async def generate_tts_audio(
    text: str, 
    voice: str = "nova",
    model: str = "tts-1",
    speed: float = 1.0
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate TTS audio using OpenAI via Emergent LLM Key.
    Returns (base64_audio, error_message)
    
    Voices: alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer
    Models: tts-1 (fast), tts-1-hd (high quality)
    """
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        tts = OpenAITextToSpeech(api_key=api_key)
        
        # Limit text to 4096 chars
        text_chunk = text[:4096]
        
        audio_base64 = await tts.generate_speech_base64(
            text=text_chunk,
            model=model,
            voice=voice,
            speed=speed
        )
        
        return f"data:audio/mp3;base64,{audio_base64}", None
        
    except Exception as e:
        logger.error(f"TTS Error: {str(e)}")
        return None, str(e)


# =============================================================================
# IMAGE GENERATION SERVICE (Gemini Nano Banana)
# =============================================================================

async def generate_avatar_image(
    prompt: str,
    style: str = "professional educator",
    session_id: str = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate AI avatar/tutor image using Gemini Nano Banana.
    Returns (base64_image, error_message)
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        session_id = session_id or f"avatar-{datetime.now().timestamp()}"
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message="You are an expert at generating educational avatar images."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        full_prompt = f"Create a {style} avatar image: {prompt}. Make it suitable for an educational platform, professional and friendly."
        
        msg = UserMessage(text=full_prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Return first image as base64
            img_data = images[0].get('data', '')
            mime_type = images[0].get('mime_type', 'image/png')
            return f"data:{mime_type};base64,{img_data}", None
        
        return None, "No image generated"
        
    except Exception as e:
        logger.error(f"Avatar Generation Error: {str(e)}")
        return None, str(e)


async def generate_educational_visual(
    concept: str,
    visual_type: str = "diagram",
    subject: str = "general",
    session_id: str = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate educational visuals (diagrams, illustrations, simulations).
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        session_id = session_id or f"visual-{datetime.now().timestamp()}"
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message="You create clear, educational visuals for learning."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        prompts = {
            "diagram": f"Create a clear, labeled educational diagram explaining {concept} in {subject}. Use arrows and labels.",
            "illustration": f"Create a colorful educational illustration depicting {concept} in {subject}. Make it engaging for students.",
            "simulation": f"Create a visual representation simulating {concept} in {subject}. Show the process or mechanism.",
            "infographic": f"Create an infographic about {concept} in {subject}. Include key facts and visual elements.",
            "flowchart": f"Create a flowchart showing the process or steps of {concept} in {subject}."
        }
        
        prompt = prompts.get(visual_type, prompts["diagram"])
        
        msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            img_data = images[0].get('data', '')
            mime_type = images[0].get('mime_type', 'image/png')
            return f"data:{mime_type};base64,{img_data}", None
        
        return None, "No visual generated"
        
    except Exception as e:
        logger.error(f"Visual Generation Error: {str(e)}")
        return None, str(e)


# =============================================================================
# LLM CHAT SERVICE (For AI Mentor, Teaching Mode, etc.)
# =============================================================================

async def get_ai_response(
    messages: List[Dict[str, str]],
    system_prompt: str = None,
    session_id: str = None,
    model: str = "gpt-5.2"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get AI response for chat, mentoring, teaching evaluation, etc.
    Returns (response_text, error_message)
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, SystemMessage
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            return None, "EMERGENT_LLM_KEY not configured"
        
        session_id = session_id or f"chat-{datetime.now().timestamp()}"
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_prompt or "You are a helpful AI educational assistant."
        )
        
        # Process messages
        response = None
        for msg in messages:
            if msg.get('role') == 'user':
                response = await chat.send_message(UserMessage(text=msg['content']))
        
        return response, None
        
    except Exception as e:
        logger.error(f"AI Response Error: {str(e)}")
        return None, str(e)


# =============================================================================
# MICRO-HINTS AND ANALOGIES SERVICE
# =============================================================================

async def generate_micro_hint(
    concept: str,
    learner_background: str = "general",
    previous_mistakes: List[str] = None,
    hint_type: str = "perspective_shift"
) -> Dict[str, Any]:
    """
    Generate intelligent micro-hints tailored to learner's background and mistakes.
    """
    system_prompt = f"""You are an expert educational coach. Generate a 30-second hint for understanding a concept.
    
    Learner Background: {learner_background}
    Previous Mistakes: {', '.join(previous_mistakes or [])}
    
    Your hint should:
    1. Be concise (30 seconds to read)
    2. Shift the learner's perspective
    3. Connect to their background knowledge
    4. Avoid repeating past unsuccessful approaches
    5. Be encouraging but not condescending
    """
    
    prompt = f"Generate a {hint_type} hint for understanding: {concept}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"hint": None, "error": error}
    
    return {
        "hint": response,
        "hint_type": hint_type,
        "duration_seconds": 30,
        "concept": concept
    }


async def generate_analogy(
    concept: str,
    learner_background: str = "general",
    interests: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a personalized analogy based on learner's background and interests.
    """
    interests_str = ', '.join(interests or ['everyday life'])
    
    system_prompt = f"""You are an expert at creating memorable analogies for learning.
    
    Learner Background: {learner_background}
    Interests: {interests_str}
    
    Create an analogy that:
    1. Connects the concept to something familiar from their interests
    2. Is accurate and doesn't create misconceptions
    3. Is memorable and creative
    4. Takes about 30 seconds to explain
    """
    
    prompt = f"Create an analogy explaining: {concept}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"analogy": None, "error": error}
    
    return {
        "analogy": response,
        "concept": concept,
        "tailored_to": learner_background,
        "duration_seconds": 30
    }


async def generate_comprehension_questions(
    concept: str,
    difficulty: str = "medium",
    count: int = 3
) -> Dict[str, Any]:
    """
    Generate follow-up comprehension questions for a concept.
    """
    system_prompt = """You are an expert at creating comprehension questions.
    Generate questions that:
    1. Test true understanding, not memorization
    2. Reveal misconceptions
    3. Progress from basic to deeper understanding
    
    Return as JSON array with format:
    [{"question": "...", "type": "conceptual|application|analysis", "reveals": "what misconception it might reveal"}]
    """
    
    prompt = f"Generate {count} {difficulty} comprehension questions for: {concept}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"questions": [], "error": error}
    
    # Try to parse JSON from response
    try:
        # Find JSON array in response
        start = response.find('[')
        end = response.rfind(']') + 1
        if start >= 0 and end > start:
            questions = json.loads(response[start:end])
        else:
            questions = [{"question": response, "type": "general", "reveals": "general understanding"}]
    except:
        questions = [{"question": response, "type": "general", "reveals": "general understanding"}]
    
    return {
        "questions": questions,
        "concept": concept,
        "difficulty": difficulty
    }


# =============================================================================
# SYLLABUS INGESTION SERVICE
# =============================================================================

async def analyze_syllabus_content(
    content: str,
    content_type: str = "syllabus"
) -> Dict[str, Any]:
    """
    Analyze uploaded syllabus/document and extract structured learning content.
    """
    system_prompt = """You are an expert curriculum designer. Analyze the provided educational content and extract:
    1. Main topics and subtopics
    2. Learning objectives
    3. Prerequisites
    4. Key concepts with relationships
    5. Suggested assessments
    6. Real-world applications
    
    Return as JSON with format:
    {
        "title": "course title",
        "topics": [{"name": "...", "subtopics": [...], "hours": N}],
        "objectives": ["..."],
        "prerequisites": ["..."],
        "concepts": [{"name": "...", "prerequisites": [...], "related": [...]}],
        "assessments": [{"type": "...", "topic": "...", "description": "..."}],
        "applications": ["..."]
    }
    """
    
    prompt = f"Analyze this {content_type} and extract structured learning content:\n\n{content[:8000]}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    # Parse JSON response
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_analysis": response}


async def generate_interactive_lesson(
    topic: str,
    learning_objectives: List[str],
    duration_minutes: int = 30
) -> Dict[str, Any]:
    """
    Generate an interactive lesson from a topic.
    """
    system_prompt = """You are an expert instructional designer. Create an interactive lesson plan.
    
    Return as JSON with format:
    {
        "title": "...",
        "sections": [
            {
                "title": "...",
                "type": "introduction|explanation|activity|assessment",
                "content": "...",
                "duration_minutes": N,
                "interactive_elements": ["..."],
                "visual_suggestions": ["..."]
            }
        ],
        "key_takeaways": ["..."],
        "reflection_questions": ["..."]
    }
    """
    
    objectives_str = '\n'.join(f"- {obj}" for obj in learning_objectives)
    prompt = f"""Create an interactive {duration_minutes}-minute lesson on: {topic}

Learning Objectives:
{objectives_str}

Make it engaging with activities, visuals, and interactive elements."""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_lesson": response}


# =============================================================================
# LEARN BY TEACHING MODE (AI Student Avatar)
# =============================================================================

async def simulate_student_interaction(
    teacher_explanation: str,
    concept: str,
    student_personality: str = "curious",
    mastery_level: float = 0.5
) -> Dict[str, Any]:
    """
    Simulate an AI student asking questions about a taught concept.
    The AI acts confused where the teacher's explanation is weak.
    """
    confusion_level = "high" if mastery_level < 0.3 else "medium" if mastery_level < 0.7 else "low"
    
    system_prompt = f"""You are a {student_personality} student learning about {concept}.
    
    Your behavior:
    - Confusion level: {confusion_level}
    - Ask realistic questions
    - Challenge weak explanations
    - Act confused where reasoning is unclear
    - Be encouraging when explanations are good
    
    After the teacher explains, respond with:
    1. A question or point of confusion
    2. Whether you understood (honestly)
    3. What part was clearest/most confusing
    
    Return as JSON:
    {{
        "understood": true/false,
        "question": "your question or clarification request",
        "feedback": "what was clear or confusing",
        "follow_up_needed": true/false,
        "encouragement": "positive feedback if explanation was good"
    }}
    """
    
    prompt = f"The teacher explained: {teacher_explanation}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_response": response}


async def evaluate_teaching_quality(
    explanation: str,
    concept: str,
    student_responses: List[Dict]
) -> Dict[str, Any]:
    """
    Evaluate the quality of a user's teaching explanation.
    """
    system_prompt = """You are an expert teaching evaluator. Analyze the teaching quality.
    
    Evaluate:
    1. Clarity (1-10)
    2. Accuracy (1-10)
    3. Completeness (1-10)
    4. Engagement (1-10)
    5. Use of examples (1-10)
    
    Return as JSON:
    {
        "overall_score": N,
        "scores": {"clarity": N, "accuracy": N, "completeness": N, "engagement": N, "examples": N},
        "strengths": ["..."],
        "gaps": ["..."],
        "recommendations": ["..."],
        "mastery_level": 0.0-1.0
    }
    """
    
    responses_str = json.dumps(student_responses, indent=2)
    prompt = f"""Evaluate this teaching explanation about {concept}:

Teacher's Explanation:
{explanation}

Student Responses:
{responses_str}"""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_evaluation": response}


# =============================================================================
# QUESTION GAP ANALYSIS SERVICE
# =============================================================================

async def analyze_user_question(
    question: str,
    subject: str = "general"
) -> Dict[str, Any]:
    """
    Analyze a user-created question for depth, coverage, and gaps.
    """
    system_prompt = """You are an expert at analyzing educational questions using Bloom's Taxonomy.
    
    Analyze the question for:
    1. Bloom's level (Remember, Understand, Apply, Analyze, Evaluate, Create)
    2. Conceptual coverage
    3. Hidden misconceptions
    4. Missing prerequisites
    5. Clarity and structure
    
    Return as JSON:
    {
        "blooms_level": "...",
        "blooms_score": 1-6,
        "coverage": {"topic": "...", "depth": "shallow/medium/deep", "breadth": "narrow/medium/wide"},
        "potential_misconceptions": ["..."],
        "missing_prerequisites": ["..."],
        "clarity_score": 1-10,
        "suggestions": ["..."],
        "related_topics": ["..."]
    }
    """
    
    prompt = f"Analyze this question in the context of {subject}:\n\n{question}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_analysis": response}


async def evaluate_user_answer(
    question: str,
    answer: str,
    subject: str = "general"
) -> Dict[str, Any]:
    """
    Evaluate a user's answer to their own question.
    """
    system_prompt = """You are an expert at evaluating learning comprehension.
    
    Evaluate the answer for:
    1. Correctness
    2. Completeness
    3. Hidden misunderstandings
    4. Depth of understanding
    
    Return as JSON:
    {
        "correct": true/false,
        "completeness_score": 1-10,
        "understanding_score": 1-10,
        "misunderstandings": ["..."],
        "missing_elements": ["..."],
        "feedback": "...",
        "improvement_suggestions": ["..."],
        "recommended_topics": ["..."]
    }
    """
    
    prompt = f"""Evaluate this answer in {subject}:

Question: {question}

Answer: {answer}"""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_evaluation": response}


# =============================================================================
# ASSIGNMENT AUTO-GENERATION SERVICE
# =============================================================================

async def generate_assignment(
    lesson_topic: str,
    learning_objectives: List[str],
    assignment_type: str = "reflection",
    difficulty: str = "medium"
) -> Dict[str, Any]:
    """
    Auto-generate an assignment based on lesson content.
    """
    system_prompt = f"""You are an expert at creating educational assignments.
    
    Create a {difficulty} {assignment_type} assignment that:
    1. Tests real understanding, not memorization
    2. Connects to real-world applications
    3. Encourages critical thinking
    4. Is engaging and relevant
    
    Return as JSON:
    {{
        "title": "...",
        "instructions": "...",
        "questions": [{{"question": "...", "type": "...", "points": N}}],
        "rubric": [{{"criteria": "...", "excellent": "...", "good": "...", "needs_work": "..."}}],
        "estimated_time_minutes": N,
        "resources": ["..."]
    }}
    """
    
    objectives_str = '\n'.join(f"- {obj}" for obj in learning_objectives)
    prompt = f"""Create an assignment for: {lesson_topic}

Learning Objectives:
{objectives_str}"""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_assignment": response}


async def evaluate_assignment_submission(
    assignment: Dict[str, Any],
    submission: str
) -> Dict[str, Any]:
    """
    AI evaluation of assignment submission.
    """
    system_prompt = """You are an expert at evaluating student work.
    
    Evaluate the submission:
    1. Check if requirements are met
    2. Assess understanding depth
    3. Identify misconceptions
    4. Provide constructive feedback
    
    Return as JSON:
    {
        "score": N,
        "max_score": N,
        "grade": "A/B/C/D/F",
        "strengths": ["..."],
        "areas_for_improvement": ["..."],
        "misconceptions_identified": ["..."],
        "feedback": "...",
        "knowledge_graph_updates": [{"concept": "...", "status": "mastered/learning/needs_review"}]
    }
    """
    
    prompt = f"""Evaluate this submission:

Assignment:
{json.dumps(assignment, indent=2)}

Student Submission:
{submission}"""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_evaluation": response}


# =============================================================================
# MULTI-DISCIPLINARY COURSE GENERATION
# =============================================================================

async def generate_multidisciplinary_lesson(
    topic: str,
    subjects: List[str],
    duration_minutes: int = 45
) -> Dict[str, Any]:
    """
    Generate a multi-disciplinary lesson combining multiple subjects.
    """
    subjects_str = ', '.join(subjects)
    
    system_prompt = f"""You are an expert at creating interdisciplinary educational content.
    
    Create a lesson that seamlessly integrates: {subjects_str}
    
    The lesson should:
    1. Show connections between disciplines
    2. Provide multiple perspectives on the topic
    3. Include activities from each discipline
    4. Help students see the bigger picture
    
    Return as JSON:
    {{
        "title": "...",
        "central_theme": "...",
        "disciplines": [
            {{
                "subject": "...",
                "contribution": "...",
                "key_concepts": ["..."],
                "activities": ["..."]
            }}
        ],
        "connections": [
            {{"from": "...", "to": "...", "relationship": "..."}}
        ],
        "integrated_project": {{
            "description": "...",
            "requirements": ["..."],
            "evaluation_criteria": ["..."]
        }},
        "reflection_questions": ["..."]
    }}
    """
    
    prompt = f"Create a {duration_minutes}-minute multi-disciplinary lesson on: {topic}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_lesson": response}


# =============================================================================
# ADAPTIVE IDENTITY-BASED LEARNING (AIBL)
# =============================================================================

async def analyze_learner_identity(
    user_id: str,
    interaction_history: List[Dict],
    assessment_results: List[Dict]
) -> Dict[str, Any]:
    """
    Build/update a learner's cognitive identity profile.
    """
    system_prompt = """You are an expert educational psychologist analyzing learner behavior.
    
    Based on the interaction history and assessment results, determine:
    1. Motivation profile (achievement/purpose/social/curiosity/security driven)
    2. Risk tolerance (low/medium/high)
    3. Cognitive friction points (where learning sticks)
    4. Emotional learning triggers
    5. Optimal learning conditions
    
    Return as JSON:
    {
        "motivation_profile": {
            "primary": "...",
            "secondary": "...",
            "engagement_triggers": ["..."]
        },
        "risk_tolerance": {
            "level": "low/medium/high",
            "prefers_guided": true/false,
            "challenge_threshold": 0.0-1.0
        },
        "cognitive_friction": {
            "patterns": ["..."],
            "common_mistakes": ["..."],
            "processing_style": "..."
        },
        "emotional_triggers": {
            "positive": ["..."],
            "negative": ["..."],
            "recovery_strategies": ["..."]
        },
        "optimal_conditions": {
            "pace": "fast/medium/slow",
            "format_preferences": ["..."],
            "feedback_style": "...",
            "time_of_day": "..."
        },
        "recommendations": ["..."]
    }
    """
    
    history_str = json.dumps(interaction_history[-20:], indent=2)  # Last 20 interactions
    results_str = json.dumps(assessment_results[-10:], indent=2)  # Last 10 assessments
    
    prompt = f"""Analyze this learner's cognitive identity:

Interaction History:
{history_str}

Assessment Results:
{results_str}"""
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_analysis": response}


async def personalize_content_for_identity(
    content: str,
    learner_identity: Dict,
    concept: str
) -> Dict[str, Any]:
    """
    Personalize content based on learner's cognitive identity.
    """
    motivation = learner_identity.get('motivation_profile', {}).get('primary', 'curiosity')
    risk_level = learner_identity.get('risk_tolerance', {}).get('level', 'medium')
    pace = learner_identity.get('optimal_conditions', {}).get('pace', 'medium')
    
    system_prompt = f"""You are an expert at personalizing educational content.
    
    Learner Profile:
    - Motivation: {motivation}-driven
    - Risk tolerance: {risk_level}
    - Preferred pace: {pace}
    
    Adapt the content to:
    1. Frame it according to their motivation type
    2. Adjust challenge level to their risk tolerance
    3. Match their preferred pace
    4. Use their preferred format
    
    Return the personalized content as JSON:
    {{
        "personalized_content": "...",
        "framing": "how the content was framed for motivation",
        "challenge_level": "adjusted challenge description",
        "support_elements": ["added supports based on profile"],
        "engagement_hooks": ["personalized engagement elements"]
    }}
    """
    
    prompt = f"Personalize this content about {concept}:\n\n{content}"
    
    response, error = await get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system_prompt
    )
    
    if error:
        return {"error": error}
    
    try:
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(response[start:end])
    except:
        pass
    
    return {"raw_content": response}


# =============================================================================
# OUTCOME-FIRST LEARNING (OFL) - MVP/MOCKED
# =============================================================================

def decompose_outcome(outcome: str) -> Dict[str, Any]:
    """
    Decompose an outcome into skills, habits, and proofs.
    This is a simplified MVP version.
    """
    # Predefined outcome templates for MVP
    outcome_templates = {
        "data_analyst": {
            "skills": ["Data cleaning", "SQL queries", "Statistical analysis", "Data visualization", "Business communication"],
            "habits": ["Daily practice", "Portfolio building", "Networking", "Continuous learning"],
            "proofs": ["Portfolio project", "SQL certification", "Case study presentation", "Interview simulation"],
            "milestones": [
                {"name": "Foundation", "skills": ["Data cleaning", "SQL basics"], "weeks": 4},
                {"name": "Analysis", "skills": ["Statistical analysis", "Advanced SQL"], "weeks": 4},
                {"name": "Visualization", "skills": ["Data visualization", "Dashboards"], "weeks": 3},
                {"name": "Professional", "skills": ["Business communication", "Portfolio"], "weeks": 3}
            ]
        },
        "web_developer": {
            "skills": ["HTML/CSS", "JavaScript", "React", "Backend basics", "Deployment"],
            "habits": ["Daily coding", "Project building", "Code review", "Documentation"],
            "proofs": ["Portfolio website", "Full-stack project", "GitHub activity", "Technical interview"],
            "milestones": [
                {"name": "Frontend Basics", "skills": ["HTML/CSS", "JavaScript"], "weeks": 4},
                {"name": "React", "skills": ["React", "State management"], "weeks": 4},
                {"name": "Backend", "skills": ["Backend basics", "APIs"], "weeks": 4},
                {"name": "Deployment", "skills": ["Deployment", "Portfolio"], "weeks": 2}
            ]
        },
        "default": {
            "skills": ["Core knowledge", "Practical application", "Critical thinking"],
            "habits": ["Regular study", "Practice exercises", "Reflection"],
            "proofs": ["Knowledge assessment", "Practical project", "Peer review"],
            "milestones": [
                {"name": "Foundation", "skills": ["Core knowledge"], "weeks": 4},
                {"name": "Application", "skills": ["Practical application"], "weeks": 4},
                {"name": "Mastery", "skills": ["Critical thinking"], "weeks": 4}
            ]
        }
    }
    
    # Simple keyword matching for MVP
    outcome_lower = outcome.lower()
    if "data" in outcome_lower and "analyst" in outcome_lower:
        template = outcome_templates["data_analyst"]
    elif "web" in outcome_lower or "developer" in outcome_lower:
        template = outcome_templates["web_developer"]
    else:
        template = outcome_templates["default"]
    
    return {
        "outcome": outcome,
        "skills": template["skills"],
        "habits": template["habits"],
        "proofs": template["proofs"],
        "milestones": template["milestones"],
        "estimated_weeks": sum(m["weeks"] for m in template["milestones"]),
        "pricing_model": "success_based",  # MVP mock
        "success_fee_percentage": 15  # MVP mock
    }
