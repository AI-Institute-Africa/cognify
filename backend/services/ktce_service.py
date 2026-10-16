"""
Knowledge Time Compression Engine (KTCE)
Minimizes time-to-competence while preserving correctness.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

KTCE_SYSTEM_PROMPT = """You are a Knowledge Time Compression Engine (KTCE) embedded in an advanced e-learning platform with a concept-level knowledge graph.

Your primary objective is to MINIMIZE TIME-TO-COMPETENCE while PRESERVING CORRECTNESS.

You do NOT teach exhaustively.
You teach only what is necessary for the learner to perform correctly.

────────────────────────
KTCE PRINCIPLES (MANDATORY)
────────────────────────
1. Prefer decision-making ability over content coverage.
2. Skip concepts already mastered or confidently inferred.
3. Collapse linear prerequisite chains when safe.
4. Deliver the smallest viable explanation first (essence-level).
5. Expand only when learner confidence or performance requires it.
6. Optimize for action, not memorization.

────────────────────────
TASK
────────────────────────
1. Identify goal-relevant concepts in the graph.
2. Traverse prerequisites backward from those concepts.
3. Exclude concepts where:
   - status = Mastered
   - OR confidence_percentage ≥ 80
4. Infer mastery where possible and exclude if confidence is high.
5. Detect linear prerequisite chains that can be safely collapsed.
6. Produce the Minimum Viable Concept Set required for the learner to act correctly.
7. For each included concept, generate:
   - an essence-level explanation (max 2 sentences)
   - a decision rule usable in problem-solving or application

────────────────────────
OUTPUT (JSON ONLY — NO EXTRA TEXT)
────────────────────────
{
  "minimum_viable_concepts": [
    {
      "concept_id": "string",
      "concept_name": "string",
      "essence": "1–2 sentence compressed explanation",
      "decision_rule": "If X, then Y"
    }
  ],
  "collapsed_concept_groups": [
    {
      "group_name": "string",
      "included_concepts": ["concept_id"],
      "representation_type": "framework | checklist | heuristic"
    }
  ],
  "excluded_concepts": [
    {
      "concept_id": "string",
      "reason": "mastered | inferred | low operational value"
    }
  ],
  "estimated_time_to_competence_minutes": number
}"""


async def process_ktce_learning_path(
    course_id: str,
    learner_goal: str,
    knowledge_graph: List[Dict],
    gemini_chat_func
) -> Dict[str, Any]:
    """
    Process a learning path using KTCE principles.
    
    Args:
        course_id: The course identifier
        learner_goal: What the learner wants to achieve
        knowledge_graph: List of concept nodes with prerequisites and mastery info
        gemini_chat_func: The async function to call Gemini AI
    
    Returns:
        KTCE output with minimum viable concepts and learning path
    """
    try:
        # Format the knowledge graph for the prompt
        graph_text = json.dumps(knowledge_graph, indent=2)
        
        user_prompt = f"""Course: {course_id}

Learner goal: {learner_goal}

Knowledge graph (course-scoped subgraph):
{graph_text}

Analyze this knowledge graph and produce the KTCE-optimized learning path. Return ONLY valid JSON."""

        messages = [
            {"role": "system", "content": KTCE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await gemini_chat_func(messages)
        
        # Parse the JSON response
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            result = json.loads(cleaned.strip())
            
            # Validate structure
            if "minimum_viable_concepts" not in result:
                result["minimum_viable_concepts"] = []
            if "collapsed_concept_groups" not in result:
                result["collapsed_concept_groups"] = []
            if "excluded_concepts" not in result:
                result["excluded_concepts"] = []
            if "estimated_time_to_competence_minutes" not in result:
                result["estimated_time_to_competence_minutes"] = len(result["minimum_viable_concepts"]) * 5
            
            return result
            
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured fallback
            logger.warning(f"KTCE JSON parse failed, using fallback. Response: {response[:200]}")
            return _generate_fallback_ktce(knowledge_graph, learner_goal)
            
    except Exception as e:
        logger.error(f"KTCE processing error: {e}")
        return _generate_fallback_ktce(knowledge_graph, learner_goal)


def _generate_fallback_ktce(knowledge_graph: List[Dict], learner_goal: str) -> Dict[str, Any]:
    """Generate a fallback KTCE response based on simple analysis."""
    
    # Filter to concepts not yet mastered
    concepts_to_learn = []
    excluded = []
    
    for concept in knowledge_graph:
        status = concept.get("status", "Not Started")
        confidence = concept.get("confidence_percentage", 0)
        
        if status == "Mastered" or confidence >= 80:
            excluded.append({
                "concept_id": concept.get("concept_id", concept.get("id", "")),
                "reason": "mastered" if status == "Mastered" else "high confidence"
            })
        else:
            concepts_to_learn.append({
                "concept_id": concept.get("concept_id", concept.get("id", "")),
                "concept_name": concept.get("concept_name", concept.get("name", "Unknown")),
                "essence": f"Core concept for understanding {concept.get('concept_name', 'this topic')}.",
                "decision_rule": f"Apply {concept.get('concept_name', 'this')} when working with related problems."
            })
    
    # Limit to top 10 most important
    concepts_to_learn = concepts_to_learn[:10]
    
    return {
        "minimum_viable_concepts": concepts_to_learn,
        "collapsed_concept_groups": [],
        "excluded_concepts": excluded,
        "estimated_time_to_competence_minutes": len(concepts_to_learn) * 5,
        "learner_goal": learner_goal,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def calculate_concept_priority(concept: Dict, goal_keywords: List[str]) -> float:
    """Calculate priority score for a concept based on goal relevance."""
    score = 0.0
    
    concept_name = concept.get("concept_name", "").lower()
    
    # Check goal keyword matches
    for keyword in goal_keywords:
        if keyword.lower() in concept_name:
            score += 2.0
    
    # Penalize already learned concepts
    confidence = concept.get("confidence_percentage", 0)
    if confidence >= 80:
        score -= 5.0
    elif confidence >= 50:
        score -= 2.0
    
    # Prioritize concepts with fewer prerequisites (entry points)
    prereqs = concept.get("prerequisites", [])
    if len(prereqs) == 0:
        score += 1.0
    
    return score


async def generate_compressed_lesson(
    concept: Dict,
    gemini_chat_func,
    learner_context: str = ""
) -> Dict[str, Any]:
    """
    Generate a KTCE-compressed lesson for a single concept.
    
    Returns:
        {
            "essence": "1-2 sentence core explanation",
            "decision_rule": "If X, then Y actionable rule",
            "example": "Brief concrete example",
            "verification_question": "Quick check question"
        }
    """
    try:
        prompt = f"""Generate a KTCE-compressed lesson for this concept:

Concept: {concept.get('concept_name', 'Unknown')}
Description: {concept.get('description', 'No description')}
Learner Context: {learner_context}

Provide ONLY this JSON structure:
{{
  "essence": "1-2 sentence core explanation that captures the most important idea",
  "decision_rule": "If [condition], then [action] - a practical rule for applying this concept",
  "example": "Brief concrete example (1-2 sentences)",
  "verification_question": "Quick question to verify understanding"
}}"""

        response = await gemini_chat_func([{"role": "user", "content": prompt}])
        
        # Parse response
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        
        return json.loads(cleaned.strip())
        
    except Exception as e:
        logger.error(f"Compressed lesson generation error: {e}")
        return {
            "essence": f"{concept.get('concept_name', 'This concept')} is a fundamental building block for this topic.",
            "decision_rule": "Apply this concept when encountering related problems.",
            "example": "See course materials for examples.",
            "verification_question": f"Can you explain {concept.get('concept_name', 'this concept')} in your own words?"
        }
