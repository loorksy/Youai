from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    api_keys: Optional[Dict[str, Any]] = Field(default_factory=dict)

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Video(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    topic: str
    title: str
    description: str
    hashtags: List[str]
    dimensions: str
    video_length: str
    voice: Optional[str] = None
    background_music: bool = False
    character_image_url: Optional[str] = None
    ai_generator: str
    script: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str = "pending"
    youtube_video_id: Optional[str] = None
    schedule_type: str = "immediate"
    scheduled_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    analytics: Optional[Dict[str, Any]] = Field(default_factory=dict)

class VideoCreate(BaseModel):
    topic: str
    dimensions: str
    video_length: str
    ai_generator: str
    voice: Optional[str] = None
    background_music: bool = False
    character_image_url: Optional[str] = None
    schedule_type: str = "immediate"
    scheduled_time: Optional[str] = None
    content_provider: Optional[str] = "gemini"
    selected_model: Optional[str] = None
    model_purpose: Optional[str] = "content_generation"

class Campaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    topic: str
    status: str = "active"
    frequency: str
    videos_generated: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class APIConnection(BaseModel):
    service: str
    status: str
    message: str

class APIKeyUpdate(BaseModel):
    service: str
    credentials: Dict[str, Any]

class TrendingTopic(BaseModel):
    topic: str
    views: int
    engagement_rate: float
    related_keywords: List[str]