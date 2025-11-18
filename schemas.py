"""
Database Schemas for Premanand Maharaj Media Library

Each Pydantic model represents a collection in MongoDB. The collection name is the
lowercase of the class name (e.g., Video -> "video").
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime


class ScriptureRef(BaseModel):
    """Embedded schema to capture a specific scripture reference mentioned."""
    scripture: str = Field(..., description="Name of the scripture, e.g., Bhagavad Gita, Srimad Bhagavatam")
    chapter: Optional[str] = Field(None, description="Chapter number/name if applicable")
    verses: Optional[str] = Field(None, description="Verse or range, e.g., 2.47 or 1.2.10-12")
    quote: Optional[str] = Field(None, description="Quoted line or summary from the scripture")
    notes: Optional[str] = Field(None, description="Any additional context")


class Video(BaseModel):
    """Videos/Reels collection schema.
    Collection: "video"
    """
    title: str = Field(..., description="Video title")
    platform: str = Field(..., description="youtube | instagram | other")
    youtube_id: Optional[str] = Field(None, description="YouTube video ID if platform is youtube")
    url: HttpUrl = Field(..., description="Full URL to the video/reel")
    thumbnail: Optional[HttpUrl] = Field(None, description="Thumbnail image URL")
    published_at: Optional[datetime] = Field(None, description="Original publish date")
    tags: List[str] = Field(default_factory=list, description="Keywords for search and filtering")
    scriptures: List[ScriptureRef] = Field(default_factory=list, description="Scriptures mentioned in this media")
    speaker: str = Field("Premanand Maharaj", description="Speaker name")
    language: Optional[str] = Field(None, description="Primary language of discourse")
    duration_seconds: Optional[int] = Field(None, ge=0, description="Duration in seconds, if known")


# Example of an additional collection if needed in future
class Playlist(BaseModel):
    name: str
    description: Optional[str] = None
    video_ids: List[str] = Field(default_factory=list)
