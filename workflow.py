# LangChain LLM chains — classification, reply, critique, refine, summary, questions

import json
import os
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import settings


def load_prompts():
    """Load prompt templates from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path) as f:
        return json.load(f)["prompts"]


def get_llm():
    """Select LLM provider based on settings (groq or mistral)."""
    if settings.LLM_PROVIDER == "groq":
        return ChatGroq(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.GROQ_API_KEY,
        )
    elif settings.LLM_PROVIDER == "mistral":
        return ChatMistralAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.MISTRAL_API_KEY,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")


llm = get_llm()
parser = StrOutputParser()
prompts = load_prompts()

# Chain 1: Classify email into important/spam/work/personal/unimportant
classify_prompt = ChatPromptTemplate.from_messages([
    ("system", "You classify emails into exactly one category: important, spam, work, personal, unimportant. Return ONLY the category name."),
    ("human", """From: {from_addr}
To: {to}
Subject: {subject}
Body: {body_preview}
Date: {date}
Has Attachments: {hasAttachments}

Category:"""),
])

classification_chain = classify_prompt | llm | parser

# Chain 2: Generate a reply draft for an email
reply_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI email assistant. Generate a professional, concise reply draft."),
    ("human", """Original Email:
From: {from_addr}
Subject: {subject}
Body: {body}

{thread_context}

Tone: {tone}
{instructions}

Generate reply:"""),
])

reply_chain = reply_prompt | llm | parser

# Chain 3: Score a generated reply (critique phase)
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "Score the email reply quality from 1-10. Return ONLY the number."),
    ("human", """Original: {original}
Reply: {reply}

Score:"""),
])

critic_chain = critic_prompt | llm | parser

# Chain 4: Improve the reply based on the critique score (refine phase)
refine_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve the email reply based on the critique. The previous score was {score}/10."),
    ("human", """Original Email: {original}
Current Reply: {reply}
Critique Score: {score}

Improved reply:"""),
])

refine_chain = refine_prompt | llm | parser

# Chain 5: Summarize an email (prompt loaded from config.json)
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", prompts["email_summary"]["system"]),
    ("human", prompts["email_summary"]["template"]),
])
summary_chain = summary_prompt | llm | parser

# Chain 6: Generate a question from an email (prompt loaded from config.json)
question_prompt = ChatPromptTemplate.from_messages([
    ("system", prompts["question_generation"]["system"]),
    ("human", prompts["question_generation"]["template"]),
])
question_chain = question_prompt | llm | parser
