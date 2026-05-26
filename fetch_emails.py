# Standalone script: fetch up to 100 emails from Gmail proxy,
# store in MongoDB, and save a raw JSON dump.

import asyncio
import json
import base64
import email
from datetime import datetime
from typing import Optional
import httpx

from config import settings
from database import db
from crud import create_email


def decode_base64(data: str) -> str:
    """Decode base64url (RFC 4648) email body content, with padding fix."""
    if not data:
        return ""
    try:
        padded = data + "=" * (4 - len(data) % 4) if len(data) % 4 else data
        return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
    except Exception:
        try:
            return base64.b64decode(padded).decode("utf-8", errors="replace")
        except Exception:
            return data


def extract_header(headers: list, name: str) -> str:
    """Find a named header (e.g. 'From', 'Subject') from the Gmail API headers list."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def extract_body(payload: dict) -> str:
    """Recursively extract text/plain (or text/html) body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        return decode_base64(payload.get("body", {}).get("data", ""))
    if mime == "text/html":
        return decode_base64(payload.get("body", {}).get("data", ""))
    parts = payload.get("parts", [])
    if not parts:
        return decode_base64(payload.get("body", {}).get("data", ""))
    for part in parts:
        result = extract_body(part)
        if result:
            return result
    return ""


def parse_date(date_str: str) -> datetime:
    """Parse RFC 2822 date string to timezone-naive datetime."""
    if not date_str:
        return datetime.now()
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.replace(tzinfo=None)
    except Exception:
        return datetime.now()


def parse_to_list(header_val: str) -> list:
    """Parse a comma-separated address header into a list of email addresses."""
    if not header_val:
        return []
    addresses = email.utils.getaddresses([header_val])
    return [addr[1] for addr in addresses if addr[1]]


async def fetch_emails(max_results: int = 100, q: Optional[str] = None):
    """Main fetch routine: list messages, get full detail for each, store in Mongo + JSON."""
    proxy_url = settings.GMAIL_PROXY_URL
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{proxy_url}/messages",
            params={"maxResults": max_results, "q": q},
        )
        resp.raise_for_status()
        message_list = resp.json()

    print(f"Found {len(message_list)} messages")
    raw_emails = []
    stored_count = 0

    for i, msg_ref in enumerate(message_list):
        msg_id = msg_ref.get("id")
        if not msg_id:
            continue

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{proxy_url}/messages/{msg_id}")
            resp.raise_for_status()
            msg = resp.json()

        payload = msg.get("payload", {})
        headers = payload.get("headers", [])

        from_addr = extract_header(headers, "From")
        to_val = extract_header(headers, "To")
        cc_val = extract_header(headers, "Cc")
        subject = extract_header(headers, "Subject")
        date_str = extract_header(headers, "Date")
        parsed_date = parse_date(date_str)

        body = extract_body(payload)

        # Fall back to internalDate (epoch ms) if Date header is missing
        internal_date = msg.get("internalDate", "")
        if internal_date and not date_str:
            try:
                ts = int(internal_date) / 1000
                parsed_date = datetime.fromtimestamp(ts)
            except Exception:
                pass

        label_ids = msg.get("labelIds", [])

        # Detect attachments: check payload parts or label hints
        has_attachments = any(
            p.get("filename") and p.get("filename") != ""
            for p in payload.get("parts", [])
        ) or "ATTACHMENTS" in label_ids or "HAS_ATTACHMENT" in label_ids

        raw_email = {
            "gmailId": msg.get("id"),
            "threadId": msg.get("threadId"),
            "from": from_addr,
            "to": parse_to_list(to_val),
            "cc": parse_to_list(cc_val),
            "subject": subject,
            "body": body,
            "date": parsed_date.isoformat(),
            "snippet": msg.get("snippet", ""),
            "labels": label_ids,
            "hasAttachments": has_attachments,
            "classification": "unimportant",
            "importanceScore": 0,
            "isRead": "UNREAD" not in label_ids,
            "tags": [],
            "internalDate": internal_date,
        }

        raw_emails.append(raw_email)

        # Store in MongoDB
        email_data = raw_email.copy()
        email_data["date"] = parsed_date
        result = await create_email(email_data)
        if result["status"] == "created":
            stored_count += 1

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(message_list)} emails")

    # Write raw JSON dump
    raw_file = f"raw_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(raw_file, "w") as f:
        json.dump(raw_emails, f, indent=2, default=str)

    print(f"\nDone! Saved raw file: {raw_file}")
    print(f"Stored {stored_count} new emails in MongoDB (skipped {len(raw_emails) - stored_count} duplicates)")
    return raw_emails


if __name__ == "__main__":
    asyncio.run(fetch_emails(max_results=100))
