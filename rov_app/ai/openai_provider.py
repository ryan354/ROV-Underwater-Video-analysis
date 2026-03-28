"""OpenAI AI provider (GPT-4o, GPT-4o-mini with vision)."""

import base64
import requests
import logging

from rov_app.ai.base_provider import AIProvider

log = logging.getLogger(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(AIProvider):
    name = "openai"

    def analyze_frame(self, image_path, telemetry, cv_flags,
                      api_key, model_id, max_tokens=700,
                      enable_detection=False, detection_mode="precise"):
        prompt = self._build_prompt(telemetry, cv_flags, enable_detection, detection_mode)

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{img_b64}",
                                   "detail": "high"}},
                    {"type": "text", "text": prompt}
                ]
            }]
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        try:
            r = requests.post(OPENAI_URL, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"].strip()
            log.debug(f"Raw AI response (first 500 chars): {raw[:500]}")
            return self._parse_response(raw)
        except Exception as e:
            log.error(f"Raw response preview: {raw[:300] if 'raw' in dir() else 'N/A'}")
            return self._error_fallback(e)
