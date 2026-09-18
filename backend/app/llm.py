import base64
from typing import Any

import httpx

from app.config import settings

XAI_BASE = "https://api.x.ai/v1"
OPENAI_BASE = "https://api.openai.com/v1"

VISION_SYSTEM = """Izvuci polja sa skena srpske isprave. Nije pravna overa originala.

Vrati isključivo JSON:
{"readable":true,"type":"licna_karta","expiry":"2026-03-01","name":null,"issuing_place":null,"address":null}

type sme biti samo: licna_karta, pasos, vozacka_dozvola, izvod_rodjeni, uverenje_drzavljanstvo, zdravstvena_isprava, saobracajna_dozvola, polisa_osiguranja, tehnicki_pregled, uplatnica_euprava, dokaz_pravnog_osnova, saglasnost_vlasnika, saglasnost_roditelja, lekarsko_vozac, dokaz_ispit_voznje, apr_obrazac. Inače null.
expiry je YYYY-MM-DD ili null. Ako je datum samo mesec/godina, koristi poslednji dan tog meseca.
Ako slika nije čitljiva ili nije isprava: readable=false i type=null.
Ne izmišljaj rok. name/address samo ako pišu na skenu.
"""


def ping_xai() -> dict[str, str | bool]:
    """Cheap connectivity check. Does not send user PII."""
    if not settings.xai_api_key:
        return {
            "configured": False,
            "ok": False,
            "detail": "XAI_API_KEY nije postavljen",
            "model": settings.xai_model,
        }
    try:
        response = httpx.get(
            f"{XAI_BASE}/models",
            headers={"Authorization": f"Bearer {settings.xai_api_key}"},
            timeout=15.0,
        )
        if response.status_code >= 400:
            return {
                "configured": True,
                "ok": False,
                "detail": f"xAI HTTP {response.status_code}",
                "model": settings.xai_model,
            }
        return {
            "configured": True,
            "ok": True,
            "detail": "xAI models OK",
            "model": settings.xai_model,
        }
    except httpx.HTTPError:
        return {
            "configured": True,
            "ok": False,
            "detail": "xAI unreachable",
            "model": settings.xai_model,
        }


def complete_xai(
    system: str,
    user: str,
    *,
    json_object: bool = True,
    timeout: float = 15.0,
    max_tokens: int = 800,
) -> str:
    """Chat Completions for matching. Never log `user` — may contain PII."""
    if not settings.xai_api_key:
        raise RuntimeError("XAI_API_KEY nije postavljen")
    payload: dict[str, Any] = {
        "model": settings.xai_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if json_object:
        payload["response_format"] = {"type": "json_object"}
    try:
        response = httpx.post(
            f"{XAI_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {settings.xai_api_key}"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])
    except httpx.HTTPError as exc:
        raise RuntimeError("xAI matching failed") from exc


def extract_document_openai_vision(
    image_bytes: bytes,
    *,
    mime: str = "image/jpeg",
    timeout: float = 20.0,
) -> dict[str, object]:
    """OpenAI Vision → JSON polja. Nikad ne loguj sliku ni ime fajla."""
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY nije postavljen")
    encoded = base64.b64encode(image_bytes).decode("ascii")
    payload: dict[str, Any] = {
        "model": settings.openai_vision_model,
        "messages": [
            {"role": "system", "content": VISION_SYSTEM},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Pročitaj tip isprave i datum važenja sa slike.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{encoded}"},
                    },
                ],
            },
        ],
        "temperature": 0,
        "max_tokens": 400,
        "response_format": {"type": "json_object"},
    }
    try:
        response = httpx.post(
            f"{OPENAI_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return {"raw": str(data["choices"][0]["message"]["content"])}
    except httpx.HTTPError as exc:
        raise RuntimeError("OpenAI Vision failed") from exc
