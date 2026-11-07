"""Eén vraag aan een taalmodel via OpenRouter, met het antwoord in een vaste vorm (JSON).

Lukt het niet (geen sleutel, netwerkfout, ongeldig antwoord), dan geeft ask() None terug en
kiest de aanroeper zelf een fallback. De app loopt dus nooit vast door het LLM.
"""

import logging
import time
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from needful.settings import Settings

log = logging.getLogger(__name__)

URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_S = 30


def parse_answer[T: BaseModel](data: dict[str, Any], answer: type[T]) -> T | None:
    """Haal de JSON uit het antwoord van OpenRouter en controleer ze met het Pydantic-model."""
    try:
        return answer.model_validate_json(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError, ValidationError) as error:
        log.warning("ongeldig antwoord van het LLM: %s", error)
        return None


async def ask[T: BaseModel](system: str, prompt: str, answer: type[T]) -> T | None:
    """Stel de vraag; het antwoord moet de vorm van `answer` hebben, anders None."""
    settings = Settings()
    if not settings.openrouter_api_key:
        log.info("geen OPENROUTER_API_KEY, LLM overgeslagen")
        return None
    body = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        # het model moet antwoorden in precies de vorm van het Pydantic-model
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": answer.__name__,
                "strict": True,
                "schema": answer.model_json_schema(),
            },
        },
        # enkel providers die response_format echt ondersteunen
        "provider": {"require_parameters": True},
    }
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}", "X-Title": "needful."}
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            response = await client.post(URL, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as error:
        log.warning("LLM-vraag mislukt (%s): %s", settings.openrouter_model, error)
        return None
    # usage = tokens en kost: de basis voor de admin-module later
    log.info(
        "LLM %s: %.1f s, gebruik %s",
        settings.openrouter_model,
        time.perf_counter() - start,
        data.get("usage"),
    )
    return parse_answer(data, answer)
