import os
import json
from typing import Optional, Dict, Any
from openai import OpenAI


try:
    from config import OPENAI_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = None


def ai_extract_parameters(user_text: str) -> Optional[Dict[str, Any]]:
    """Calls OpenAI to extract normalized parameters from free-form user text.

    Returns dict with keys: kind ("vbelt"|"synchronous"|"unknown"), length_mm (float|None),
    profile (str|None), width_mm (float|None). Returns None on failure.
    """
    # Mock-режим: если задан OPENAI_MOCK_JSON — возвращаем его без запросов к OpenAI
    mock_payload = os.getenv("OPENAI_MOCK_JSON")
    if mock_payload:
        try:
            data = json.loads(mock_payload)
            return {
                "kind": data.get("kind", "unknown"),
                "length_mm": data.get("length_mm"),
                "profile": (data.get("profile") or None),
                "width_mm": data.get("width_mm"),
            }
        except Exception:
            return None

    # Сначала проверяем config.py, затем переменную окружения
    api_key = CONFIG_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        # print("[AI] OpenAI API ключ не найден")
        return None

    # print(f"[AI] Используется OpenAI API ключ (длина: {len(api_key) if api_key else 0})")
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "Ты помощник по нормализации запросов о ремнях. Верни JSON с полями: "
        "kind ('vbelt'|'synchronous'|'unknown'), length_mm (число или null), "
        "profile (строка или null), width_mm (число или null). "
        "Если длина в дюймах (классика A/B/C/D/E), не конвертируй (оставь число как есть), "
        "конвертацию сделает приложение. Не добавляй лишних полей."
    )

    user_prompt = f"Текст пользователя: {user_text} \nОтветь только JSON."

    try:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        max_tokens_env = os.getenv("OPENAI_MAX_TOKENS")
        max_tokens = int(max_tokens_env) if (max_tokens_env and max_tokens_env.isdigit()) else 128
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        # print(f"[AI] OpenAI ответ: {content[:200]}...") 
    except Exception as e:
        # print(f"[AI] Ошибка при вызове OpenAI: {type(e).__name__}: {e}")
        return None

    try:
        txt = content.strip()
        if txt.startswith("```"):
            txt = txt.strip('`')
        if not txt.startswith('{'):
            start = txt.find('{')
            end = txt.rfind('}')
            if start != -1 and end != -1 and end > start:
                txt = txt[start:end+1]
        data = json.loads(txt)
        kind = data.get("kind")
        length_mm = data.get("length_mm")
        profile = data.get("profile")
        width_mm = data.get("width_mm")
        return {
            "kind": kind if kind in ("vbelt", "synchronous", "unknown") else "unknown",
            "length_mm": float(length_mm) if isinstance(length_mm, (int, float, str)) and str(length_mm).replace('.', '', 1).isdigit() else None,
            "profile": str(profile).upper() if profile else None,
            "width_mm": float(width_mm) if isinstance(width_mm, (int, float, str)) and str(width_mm).replace('.', '', 1).isdigit() else None,
        }
    except Exception as e:
        # print(f"[AI] Ошибка при парсинге JSON ответа OpenAI: {type(e).__name__}: {e}")
        return None


