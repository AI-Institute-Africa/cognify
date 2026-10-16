"""Knowledge graph and learning models"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid
from .enums import ContentType, ConceptStatus

class Concept(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    subject: str
    grade_level: str
    prerequisites: List[str] = []
    dependencies: List[str] = []
    cross_links: List[str] = []
    real_world_apps: List[str] = []
    learning_objectives: List[str] = []
    content_modules: List[str] = []
    assessment_criteria: List[str] = []
    estimated_hours: float = 1.0
    difficulty: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LearnerConceptState(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    concept_id: str
    status: ConceptStatus = ConceptStatus.NOT_STARTED
    mastery_level: float = 0.0
    time_spent_minutes: int = 0
    attempts: int = 0
    last_assessment_score: Optional[float] = None
    notes: List[str] = []
    feynman_explanation: Optional[str] = None
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MentorProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    mentor_name: str = "EduOS Mentor"
    personality: str = "friendly"
    avatar_url: Optional[str] = None
    voice_id: Optional[str] = None
    preferred_subjects: List[str] = []
    conversation_style: str = "socratic"
    encouragement_level: str = "high"
    language: str = "en"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MentorConversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subject: Optional[str] = None
    concept_id: Optional[str] = None
    messages: List[dict] = []
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

class ContentModule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    concept_id: str
    title: str
    content_type: ContentType
    content_url: Optional[str] = None
    content_text: Optional[str] = None
    language: str = "en"
    translations: Dict[str, str] = {}
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    images: List[str] = []
    duration_minutes: int = 0
    difficulty: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VoiceProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    voice_id: str
    is_cloned: bool = False
    clone_source: Optional[str] = None
    sample_urls: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SyllabusUpload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    filename: str
    file_url: str
    status: str = "processing"
    extracted_concepts: List[str] = []
    generated_modules: List[str] = []
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
