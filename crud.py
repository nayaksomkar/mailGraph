# Async MongoDB CRUD operations for emails, drafts, and tags

from datetime import datetime
from typing import List, Optional
from database import db
from schemas import EmailResponse, DraftResponse, TagResponse, EmailClassification, DraftStatus

# ── Email CRUD ──────────────────────────────────────────────────────

async def create_email(email_data: dict) -> dict:
    """Insert email if it doesn't already exist (dedup by gmailId)."""
    existing = await db.emails.find_one({"gmailId": email_data["gmailId"]})
    if existing:
        return {"id": str(existing["_id"]), "status": "exists"}
    result = await db.emails.insert_one(email_data)
    return {"id": str(result.inserted_id), "status": "created"}

async def find_emails(
    classification: Optional[str] = None,
    tags: Optional[List[str]] = None,
    isRead: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
) -> list:
    """List emails with optional filters, sorted by date descending."""
    query = {}
    if classification:
        query["classification"] = classification
    if tags:
        query["tags"] = {"$all": tags}
    if isRead is not None:
        query["isRead"] = isRead
    cursor = db.emails.find(query).sort("date", -1).skip(offset).limit(limit)
    return await cursor.to_list(length=limit)

async def find_email_by_gmail_id(gmailId: str) -> Optional[dict]:
    """Lookup a single email by its Gmail message ID."""
    return await db.emails.find_one({"gmailId": gmailId})

async def find_emails_by_thread(threadId: str) -> list:
    """Get all emails belonging to a thread, sorted chronologically."""
    cursor = db.emails.find({"threadId": threadId}).sort("date", 1)
    return await cursor.to_list(length=100)

async def update_email(gmailId: str, updates: dict) -> Optional[dict]:
    """Update fields on an email (e.g. classification, isRead)."""
    result = await db.emails.find_one_and_update(
        {"gmailId": gmailId}, {"$set": updates}, return_document="after"
    )
    return result

async def search_emails(query: str, limit: int = 50) -> list:
    """Full-text search across email body/subject using MongoDB text index."""
    cursor = db.emails.find(
        {"$text": {"$search": query}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
    return await cursor.to_list(length=limit)

# ── Draft CRUD ──────────────────────────────────────────────────────

async def create_draft(draft_data: dict) -> str:
    """Save a new AI-generated draft."""
    result = await db.drafts.insert_one(draft_data)
    return str(result.inserted_id)

async def find_drafts(status: Optional[str] = None) -> list:
    """List drafts, optionally filtered by status."""
    query = {"status": status} if status else {}
    cursor = db.drafts.find(query).sort("createdAt", -1)
    return await cursor.to_list(length=100)

async def find_draft_by_id(draft_id: str) -> Optional[dict]:
    """Get a single draft by its MongoDB ObjectId."""
    from bson import ObjectId
    try:
        return await db.drafts.find_one({"_id": ObjectId(draft_id)})
    except Exception:
        return None

async def update_draft(draft_id: str, updates: dict) -> Optional[dict]:
    """Update a draft's fields (status, body, etc.)."""
    from bson import ObjectId
    return await db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)}, {"$set": updates}, return_document="after"
    )

# ── Tag CRUD ────────────────────────────────────────────────────────

async def create_tag(tag_data: dict) -> str:
    """Create a new classification tag."""
    result = await db.tags.insert_one(tag_data)
    return str(result.inserted_id)

async def find_tags() -> list:
    """List all tags sorted alphabetically."""
    cursor = db.tags.find().sort("name", 1)
    return await cursor.to_list(length=100)

async def update_tag(tag_id: str, updates: dict) -> Optional[dict]:
    """Update a tag's name/color/description."""
    from bson import ObjectId
    return await db.tags.find_one_and_update(
        {"_id": ObjectId(tag_id)}, {"$set": updates}, return_document="after"
    )

async def delete_tag(tag_id: str) -> bool:
    """Delete a tag by its ObjectId."""
    from bson import ObjectId
    result = await db.tags.delete_one({"_id": ObjectId(tag_id)})
    return result.deleted_count > 0
