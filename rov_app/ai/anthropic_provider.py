"""Anthropic AI provider (Claude with vision)."""

import base64
import requests
import logging

from rov_app.ai.base_provider import AIProvider

log = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider(AIProvider):
    name = "anthropic"

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
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        }
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        try:
            r = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            content = r.json()["content"]
            raw = ""
            for block in content:
                if block.get("type") == "text":
                    raw = block["text"]
                    break
            log.debug(f"Raw AI response (first 500 chars): {raw[:500]}")
            return self._parse_response(raw)
        except Exception as e:
            log.error(f"Raw response preview: {raw[:300] if 'raw' in dir() else 'N/A'}")
            return self._error_fallback(e)
