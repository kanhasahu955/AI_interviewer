"""Lightweight resume text analysis (no LLM required)."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def sanitize_resume_text(text: str | None, *, max_chars: int = 50_000) -> str:
    """Strip binary noise and cap length so VARIANT payloads stay reasonable."""
    if not text:
        return ""
    cleaned = "".join(
        ch if (ch.isprintable() or ch in "\n\t") else " " for ch in text
    )
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:max_chars]

SKILL_KEYWORDS = [
    "python",
    "javascript",
    "typescript",
    "java",
    "react",
    "node",
    "fastapi",
    "django",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "machine learning",
    "deep learning",
    "nlp",
    "langchain",
    "pytorch",
    "tensorflow",
    "git",
    "ci/cd",
    "agile",
    "scrum",
    "leadership",
    "communication",
    "problem solving",
    "system design",
    "microservices",
    "rest",
    "graphql",
    "go",
    "rust",
    "c++",
    "c#",
    ".net",
    "spring",
    "kotlin",
    "swift",
    "flutter",
    "android",
    "ios",
    "html",
    "css",
    "tailwind",
    "vue",
    "angular",
    "next.js",
    "pandas",
    "numpy",
    "spark",
    "hadoop",
    "kafka",
    "elasticsearch",
    "pinecone",
    "openai",
    "llm",
    "rag",
]


def analyze_resume_text(text: str | None) -> dict:
    """Build a structured `parsed` payload from raw resume text."""
    cleaned = sanitize_resume_text(text)
    lower = cleaned.lower()

    emails = re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", cleaned)
    phones = re.findall(
        r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}",
        cleaned,
    )

    skills = [skill for skill in SKILL_KEYWORDS if skill in lower]
    # dedupe preserving order
    seen: set[str] = set()
    unique_skills: list[str] = []
    for skill in skills:
        key = skill.lower()
        if key not in seen:
            seen.add(key)
            unique_skills.append(skill.title() if skill.islower() else skill)

    sections: list[str] = []
    for heading in ("experience", "education", "skills", "projects", "summary", "certifications"):
        if heading in lower:
            sections.append(heading.title())

    words = cleaned.split()
    return {
        "text_ready": bool(cleaned),
        "char_count": len(cleaned),
        "word_count": len(words),
        "emails": emails[:3],
        "phones": phones[:3],
        "skills_detected": unique_skills[:25],
        "sections_found": sections,
        "preview": cleaned[:3000],
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
