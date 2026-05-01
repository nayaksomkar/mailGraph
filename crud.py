from datetime import datetime
from typing import List, Optional
from database import db
from schemas import EmailResponse, DraftResponse, TagResponse, EmailClassification, DraftStatus

async def create_email(email_data: dict) -> dict:
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
    return await db.emails.find_one({"gmailId": gmailId})

async def find_emails_by_thread(threadId: str) -> list:
    cursor = db.emails.find({"threadId": threadId}).sort("date", 1)
    return await cursor.to_list(length=100)

async def update_email(gmailId: str, updates: dict) -> Optional[dict]:
    result = await db.emails.find_one_and_update(
        {"gmailId": gmailId}, {"$set": updates}, return_document="after"
    )
    return result

async def search_emails(query: str, limit: int = 50) -> list:
    cursor = db.emails.find(
        {"$text": {"$search": query}}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
    return await cursor.to_list(length=limit)

async def create_draft(draft_data: dict) -> str:
    result = await db.drafts.insert_one(draft_data)
    return str(result.inserted_id)

async def find_drafts(status: Optional[str] = None) -> list:
    query = {"status": status} if status else {}
    cursor = db.drafts.find(query).sort("createdAt", -1)
    return await cursor.to_list(length=100)

async def find_draft_by_id(draft_id: str) -> Optional[dict]:
    from bson import ObjectId
    try:
        return await db.drafts.find_one({"_id": ObjectId(draft_id)})
    except Exception:
        return None

async def update_draft(draft_id: str, updates: dict) -> Optional[dict]:
    from bson import ObjectId
    return await db.drafts.find_one_and_update(
        {"_id": ObjectId(draft_id)}, {"$set": updates}, return_document="after"
    )

async def create_tag(tag_data: dict) -> str:
    result = await db.tags.insert_one(tag_data)
    return str(result.inserted_id)

async def find_tags() -> list:
    cursor = db.tags.find().sort("name", 1)
    return await cursor.to_list(length=100)

async def update_tag(tag_id: str, updates: dict) -> Optional[dict]:
    from bson import ObjectId
    return await db.tags.find_one_and_update(
        {"_id": ObjectId(tag_id)}, {"$set": updates}, return_document="after"
    )

async def delete_tag(tag_id: str) -> bool:
    from bson import ObjectId
    result = await db.tags.delete_one({"_id": ObjectId(tag_id)})
    return result.deleted_count > 0