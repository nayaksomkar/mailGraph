from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import Optional, List
import httpx
from config import settings
from database import get_db
from crud import (
    create_email, find_emails, find_email_by_gmail_id, find_emails_by_thread,
    update_email, search_emails, create_draft, find_drafts, find_draft_by_id,
    update_draft, create_tag, find_tags, update_tag, delete_tag,
)
from schemas import (
    SyncRequest, ReplyRequest, DraftUpdate, TagCreate, TagUpdate,
    EmailResponse, DraftResponse, TagResponse, EmailClassification, DraftStatus,
)
from workflow import classification_chain, reply_chain, critic_chain, refine_chain
from logging_config import logger

app = FastAPI(title="MailGraph", description="AI Email Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "service": "mailgraph", "timestamp": datetime.now().isoformat()}

@app.get("/health")
async def health_check():
    try:
        db = get_db()
        await db.command("ping")
        db_status = True
    except Exception:
        db_status = False
    return {"status": "healthy", "db_connected": db_status}

@app.post("/emails/sync")
async def sync_emails(request: SyncRequest = Body(default=SyncRequest())):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.GMAIL_PROXY_URL}/messages",
                params={"maxResults": request.maxResults, "q": request.q},
            )
            resp.raise_for_status()
            messages = resp.json()
        count = 0
        for msg in messages:
            email_data = {
                "gmailId": msg.get("id", ""),
                "threadId": msg.get("threadId", ""),
                "from": msg.get("snippet", ""),
                "to": [],
                "subject": msg.get("snippet", ""),
                "body": msg.get("snippet", ""),
                "date": datetime.now(),
                "classification": "unimportant",
                "importanceScore": 0,
                "isRead": False,
                "tags": [],
                "labels": msg.get("labelIds", []),
                "hasAttachments": False,
                "snippet": msg.get("snippet", ""),
            }
            await create_email(email_data)
            count += 1
        return {"synced": count, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gmail sync failed: {str(e)}")

@app.get("/emails")
async def list_emails(
    classification: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    isRead: Optional[bool] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
):
    tag_list = tags.split(",") if tags else None
    return await find_emails(classification, tag_list, isRead, limit, offset)

@app.get("/emails/{gmail_id}")
async def get_email(gmail_id: str):
    email = await find_email_by_gmail_id(gmail_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email

@app.get("/emails/thread/{thread_id}")
async def get_thread(thread_id: str):
    return await find_emails_by_thread(thread_id)

@app.post("/emails/{gmail_id}/classify")
async def classify_email(gmail_id: str):
    email = await find_email_by_gmail_id(gmail_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    result = await classification_chain.ainvoke({
        "from_addr": email.get("from", ""),
        "to": ", ".join(email.get("to", [])),
        "subject": email.get("subject", ""),
        "body_preview": email.get("body", "")[:1000],
        "date": str(email.get("date", "")),
        "hasAttachments": email.get("hasAttachments", False),
    })

    classification = result.strip().lower()
    valid = ["important", "spam", "work", "personal", "unimportant"]
    classification = classification if classification in valid else "unimportant"

    await update_email(gmail_id, {"classification": classification})
    return {"gmailId": gmail_id, "classification": classification}

@app.post("/emails/{gmail_id}/reply")
async def generate_reply(gmail_id: str, request: ReplyRequest = Body(default=ReplyRequest())):
    email = await find_email_by_gmail_id(gmail_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    thread = await find_emails_by_thread(email["threadId"])
    thread_context = "\n---\n".join([f"Message: {t.get('body', '')[:500]}" for t in thread])

    draft = await reply_chain.ainvoke({
        "from_addr": email.get("from", ""),
        "subject": email.get("subject", ""),
        "body": email.get("body", ""),
        "thread_context": thread_context,
        "tone": request.userTone or "professional",
        "instructions": request.userInstructions or "",
    })

    draft_id = await create_draft({
        "emailId": gmail_id,
        "gmailId": gmail_id,
        "threadId": email["threadId"],
        "to": email.get("to", []),
        "subject": "Re: " + email.get("subject", ""),
        "body": draft,
        "aiModel": settings.LLM_MODEL,
        "reasoning": "Generated via LangGraph",
        "confidence": 0.85,
        "status": "pending",
    })

    return {"draftId": draft_id, "body": draft}

@app.get("/search")
async def search(q: str = Query(..., min_length=1)):
    return await search_emails(q)

@app.post("/emails/{gmail_id}/read")
async def mark_read(gmail_id: str):
    await update_email(gmail_id, {"isRead": True})
    return {"gmailId": gmail_id, "isRead": True}

@app.get("/drafts")
async def list_drafts(status: Optional[str] = Query(None)):
    return await find_drafts(status)

@app.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    draft = await find_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft

@app.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: str):
    return await update_draft(draft_id, {"status": "approved"})

@app.post("/drafts/{draft_id}/reject")
async def reject_draft(draft_id: str, userNotes: Optional[str] = Body("", embed=True)):
    return await update_draft(draft_id, {"status": "rejected", "userNotes": userNotes})

@app.put("/drafts/{draft_id}")
async def edit_draft(draft_id: str, request: DraftUpdate = Body(...)):
    updates = request.model_dump(exclude_unset=True)
    updates["status"] = "edited"
    return await update_draft(draft_id, updates)

@app.post("/drafts/{draft_id}/send")
async def send_draft(draft_id: str):
    draft = await find_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft["status"] not in ["approved", "edited"]:
        raise HTTPException(status_code=400, detail="Draft must be approved first")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.GMAIL_PROXY_URL}/send",
                json={
                    "to": draft["to"][0],
                    "subject": draft["subject"],
                    "body": draft["body"],
                    "threadId": draft["threadId"],
                },
            )
            resp.raise_for_status()
            result = resp.json()

        await update_draft(draft_id, {"status": "sent", "sentAt": datetime.now()})
        return {"status": "sent", "gmailMessageId": result.get("messageId")}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Send failed: {str(e)}")

@app.get("/tags")
async def list_tags():
    return await find_tags()

@app.post("/tags")
async def create_new_tag(request: TagCreate = Body(...)):
    tag_data = request.model_dump()
    tag_data["isSystem"] = False
    tag_data["usageCount"] = 0
    tag_id = await create_tag(tag_data)
    return {"id": tag_id, **tag_data}

@app.put("/tags/{tag_id}")
async def update_existing_tag(tag_id: str, request: TagUpdate = Body(...)):
    updates = request.model_dump(exclude_unset=True)
    return await update_tag(tag_id, updates)

@app.delete("/tags/{tag_id}")
async def delete_existing_tag(tag_id: str):
    success = await delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"deleted": True}