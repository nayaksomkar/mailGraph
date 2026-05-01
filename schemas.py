from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class EmailClassification(str, Enum):
    IMPORTANT = "important"
    SPAM = "spam"
    WORK = "work"
    PERSONAL = "personal"
    UNIMPORTANT = "unimportant"

class DraftStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"
    EDITED = "edited"

class TagSource(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"

class EmailCreate(BaseModel):
    gmailId: str
    threadId: str
    from_addr: str = Field(alias="from")
    to: List[str]
    cc: List[str] = []
    subject: str
    body: str
    date: datetime
    snippet: str = ""
    hasAttachments: bool = False
    labels: List[str] = []

class EmailUpdate(BaseModel):
    classification: Optional[EmailClassification] = None
    isRead: Optional[bool] = None
    tags: Optional[List[str]] = None

class EmailResponse(BaseModel):
    id: str
    gmailId: str
    threadId: str
    from_addr: str = Field(alias="from")
    to: List[str]
    subject: str
    body: str
    classification: EmailClassification
    importanceScore: int
    isRead: bool
    tags: List[str]
    date: datetime
    snippet: str

class DraftCreate(BaseModel):
    emailId: str
    gmailId: str
    threadId: str
    to: List[str]
    subject: str
    body: str
    aiModel: str = "gpt-4"
    reasoning: str = ""
    confidence: float = 0.85

class DraftUpdate(BaseModel):
    body: str
    subject: Optional[str] = None
    status: Optional[DraftStatus] = None

class DraftResponse(BaseModel):
    id: str
    emailId: str
    to: List[str]
    subject: str
    body: str
    status: DraftStatus
    aiModel: str
    reasoning: str
    confidence: float

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = None
    description: Optional[str] = None
    source: TagSource = TagSource.MANUAL

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

class TagResponse(BaseModel):
    id: str
    name: str
    color: Optional[str]
    description: Optional[str]
    isSystem: bool
    usageCount: int
    source: TagSource

class SyncRequest(BaseModel):
    maxResults: int = 50
    q: Optional[str] = None

class ReplyRequest(BaseModel):
    userTone: Optional[str] = "professional"
    userInstructions: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)