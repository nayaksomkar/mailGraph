from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import settings

def get_llm():
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

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "Score the email reply quality from 1-10. Return ONLY the number."),
    ("human", """Original: {original}
Reply: {reply}

Score:"""),
])

critic_chain = critic_prompt | llm | parser

refine_prompt = ChatPromptTemplate.from_messages([
    ("system", "Improve the email reply based on the critique. The previous score was {score}/10."),
    ("human", """Original Email: {original}
Current Reply: {reply}
Critique Score: {score}

Improved reply:"""),
])

refine_chain = refine_prompt | llm | parser