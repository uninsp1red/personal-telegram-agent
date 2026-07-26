import asyncio
import logging
import os
import voyageai
from voyageai.error import RateLimitError

logger = logging.getLogger(__name__)

MODEL = "voyage-3.5-lite"
DIMENSION = 1024

_client = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])

async def embed_with_retry(
    texts: list[str],
    input_type: str = "document",
    max_retries: int = 5,
) -> list[list[float]]:
    """Батч-эмбеддинг с retry на 429 (бесплатный тариф Voyage = 3 RPM).
    input_type: "document" при сохранении в базу, "query" при поиске"""
    for attempt in range(max_retries):
        try:
            result = await _client.embed(
                texts, model=MODEL, input_type=input_type, output_dimension=DIMENSION,
            )
            return result.embeddings
        except RateLimitError:
            wait = 20 * (attempt + 1)
            logger.warning(f"Voyage rate limit, попытка {attempt + 1}/{max_retries}, жду {wait}с")
            await asyncio.sleep(wait)
    raise RuntimeError("Не удалось получить эмбеддинги — превышен лимит запросов Voyage")