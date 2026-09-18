from typing import Any

import httpx

from app.config import settings

XAI_BASE = "https://api.x.ai/v1"


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
    timeout: float = 25.0,
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


def extract_document_openai_vision(_image_bytes: bytes) -> dict[str, str | None]:
    """Faza 3: OpenAI Vision. Matching in Faza 2 is text-only."""
    raise NotImplementedError("Vision je Faza 3")
