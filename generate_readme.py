# Generate AI-powered email summaries & questions using LLM and update README

import asyncio
import re
import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings
from database import db
from workflow import summary_chain, question_chain


def strip_html(body: str, max_chars: int = 800) -> str:
    """Strip HTML tags and return clean plain text preview."""
    if not body:
        return ""
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
    body = re.sub(r'<br\s*/?>', '\n', body)
    body = re.sub(r'<p[^>]*>', '\n', body)
    body = re.sub(r'</p>', '\n', body)
    body = re.sub(r'<[^>]+>', '', body)
    body = body.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    body = re.sub(r'&#\d+;', '', body)
    body = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u2060\u2061\u2062\u2063\u2064]', '', body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:max_chars]


async def generate_summary(from_addr: str, subject: str, body: str) -> str:
    """Use LLM to summarize an email."""
    try:
        result = await summary_chain.ainvoke({
            "from_addr": from_addr,
            "subject": subject,
            "body": strip_html(body, 1000),
        })
        return result.strip()
    except Exception as e:
        return f"AI summary unavailable ({e})"


async def generate_question(from_addr: str, subject: str, body: str) -> str:
    """Use LLM to generate a question from an email."""
    try:
        result = await question_chain.ainvoke({
            "from_addr": from_addr,
            "subject": subject,
            "body": strip_html(body, 1000),
        })
        return result.strip()
    except Exception as e:
        return f"AI question unavailable ({e})"


async def generate_readme_section(emails: list) -> str:
    """Generate the Sample Email Summaries & Inbox Q&A section."""
    lines = []
    lines.append("---\n")
    lines.append(f"### Sample Email Summaries & Inbox Q&A\n")
    lines.append(f"_AI-generated summaries and questions using {settings.LLM_PROVIDER} ({settings.LLM_MODEL})._\n")
    lines.append("")

    for i, email in enumerate(emails, 1):
        from_addr = email.get("from", "unknown")
        subject = email.get("subject", "(no subject)")
        body = email.get("body", "")

        print(f"Generating summary for email {i}/3: {subject[:50]}...")
        summary = await generate_summary(from_addr, subject, body)

        print(f"Generating question for email {i}/3...")
        question = await generate_question(from_addr, subject, body)

        lines.append(f"**📧 Email {i}**")
        lines.append(f"> **Subject:** {subject}")
        addr = from_addr.split()[-1].strip("<>") if "@" in from_addr else from_addr
        lines.append(f"> **From:** `{addr}`")
        lines.append("")
        lines.append(f"**Summary:** {summary}")
        lines.append("")
        lines.append(f"**🤔 Question:** {question}")
        lines.append("")

    return "\n".join(lines)


async def update_readme(section: str):
    """Replace the existing summary section in README with new AI-generated content."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    with open(readme_path) as f:
        content = f.read()

    # Find and replace everything from "---" before "### Sample Email Summaries" to end
    marker = "### Sample Email Summaries & Inbox Q&A"
    if marker in content:
        # Remove old section
        content = content[: content.index(marker)]
        # Remove trailing whitespace
        content = content.rstrip()
        # Remove trailing separator if any
        if content.endswith("---"):
            content = content[:-3].rstrip()
        content = content.rstrip() + "\n\n"

    content += section

    with open(readme_path, "w") as f:
        f.write(content)
    print(f"README.md updated at {readme_path}")


async def main():
    # Pick 3 non-sensitive promotional/update emails
    cursor = db.emails.find({
        "labels": {"$in": ["CATEGORY_PROMOTIONS", "CATEGORY_UPDATES"]},
    }).limit(3)
    emails = await cursor.to_list(3)

    if not emails:
        # Fallback: skip first email (usually security alert), take next 3
        cursor = db.emails.find({}).skip(1).limit(3)
        emails = await cursor.to_list(3)

    if not emails:
        print("No emails found in MongoDB. Run fetch_emails.py first.")
        return

    print(f"Processing {len(emails)} emails via {settings.LLM_PROVIDER} ({settings.LLM_MODEL})...")
    section = await generate_readme_section(emails)
    await update_readme(section)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
