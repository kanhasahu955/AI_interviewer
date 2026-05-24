from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


def embeddings_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)


def get_embedding_model():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=settings.OPENAI_API_KEY,
    )
