import json
import os
import re

import requests

API_URL = "https://router.huggingface.co/v1/chat/completions"
DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
REQUEST_TIMEOUT = 60


class HFNotConfiguredError(Exception):
    """Raised when HF_API_KEY is not set."""


class HFServiceError(Exception):
    """Raised when the HuggingFace API call fails."""


def _get_api_key() -> str:
    return (os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN") or "").strip()


def _get_model() -> str:
    return (os.getenv("HF_MODEL") or DEFAULT_MODEL).strip()


def _extract_json(content: str) -> dict:
    text = (content or "").strip()
    if not text:
        return {"recommendations": []}

    # Strip markdown fences if the model wraps JSON
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"recommendations": parsed}
    except json.JSONDecodeError:
        pass

    # Last resort: find first {...} object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {"recommendations": []}


def recommend_books_hf(user_description: str):
    api_key = _get_api_key()
    if not api_key:
        raise HFNotConfiguredError("HF_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    model = _get_model()
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a backend API that returns structured JSON.\n"
                    "Return ONLY valid JSON.\n\n"
                    "Return an object with a single key: recommendations.\n"
                    "recommendations must be an array of EXACTLY 3 objects.\n\n"
                    "Each object MUST contain:\n"
                    "- title: book title ONLY\n"
                    "- author: author name\n"
                    "- description: 1–2 factual sentences\n\n"
                    "Rules:\n"
                    "- Only REAL, well-known books\n"
                    "- No fictional books\n"
                    "- No opinions\n"
                    "- No markdown\n"
                    "- No explanations outside JSON\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f'Recommend 3 real books related to "{user_description}".\n'
                    "Respond ONLY with valid JSON."
                ),
            },
        ],
        "max_tokens": 350,
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.Timeout as exc:
        raise HFServiceError("HuggingFace request timed out") from exc
    except requests.RequestException as exc:
        raise HFServiceError(f"HuggingFace request failed: {exc}") from exc

    if response.status_code != 200:
        detail = response.text.strip()
        try:
            err_json = response.json()
            detail = (
                err_json.get("error", {}).get("message")
                or err_json.get("error")
                or err_json.get("message")
                or detail
            )
            if isinstance(detail, dict):
                detail = detail.get("message") or str(detail)
        except Exception:
            pass
        raise HFServiceError(
            f"HuggingFace HTTP {response.status_code}: {detail}"
        )

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HFServiceError(
            f"Unexpected HuggingFace response shape: {str(data)[:300]}"
        ) from exc

    parsed = _extract_json(content if isinstance(content, str) else str(content))
    recommendations = parsed.get("recommendations")
    if not isinstance(recommendations, list):
        recommendations = []

    # Normalize items so the frontend always gets title/author/description
    cleaned = []
    for item in recommendations[:3]:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "title": str(item.get("title") or "").strip(),
                "author": str(item.get("author") or "").strip(),
                "description": str(item.get("description") or "").strip(),
            }
        )

    return {"recommendations": [b for b in cleaned if b["title"]]}
