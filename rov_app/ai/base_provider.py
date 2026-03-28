"""Abstract base class for AI vision providers."""

import json
import logging
from abc import ABC, abstractmethod

from rov_app.core.telemetry import fmt_telemetry, fmt_flags
from rov_app.ai.prompt import (
    ANALYSIS_PROMPT, ANALYSIS_PROMPT_WITH_DETECTION, ANALYSIS_PROMPT_QUADRANT
)

log = logging.getLogger(__name__)


class AIProvider(ABC):
    """Base class for AI vision analysis providers."""

    name = "base"

    @abstractmethod
    def analyze_frame(self, image_path, telemetry, cv_flags,
                      api_key, model_id, max_tokens=700,
                      enable_detection=False, detection_mode="precise"):
        """
        Analyze a single frame with the AI vision model.

        Args:
            image_path: Path to the frame image
            telemetry: Telemetry dict for this frame
            cv_flags: OpenCV flags dict for this frame
            api_key: API key for the provider
            model_id: Model ID to use
            max_tokens: Maximum response tokens
            enable_detection: Whether to request bounding box/region detections
            detection_mode: "precise" (bbox coords) or "quadrant" (region names)

        Returns:
            Analysis result dict
        """
        pass

    def _build_prompt(self, telemetry, cv_flags, enable_detection=False,
                      detection_mode="precise"):
        """Build the analysis prompt with telemetry and flags."""
        telem_str = fmt_telemetry(telemetry) if telemetry else "No telemetry available"
        flags_str = fmt_flags(cv_flags) if cv_flags else "No CV signals"

        if enable_detection:
            if detection_mode == "quadrant":
                template = ANALYSIS_PROMPT_QUADRANT
            else:
                template = ANALYSIS_PROMPT_WITH_DETECTION
        else:
            template = ANALYSIS_PROMPT

        prompt = template.format(telemetry=telem_str, cv_flags=flags_str)
        return prompt

    def _parse_response(self, raw_text):
        """Parse JSON from AI response, handling markdown fences, trailing text, and truncation."""
        raw = raw_text.strip()

        # Strip markdown code fences
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                p = part.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    raw = p
                    break

        # Try direct parse first
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Extract first JSON object by finding matching braces
        start = raw.find("{")
        if start == -1:
            log.warning(f"No JSON in response: {raw[:200]}")
            raise ValueError("No JSON object found in response")

        depth = 0
        in_string = False
        i = start
        while i < len(raw):
            c = raw[i]
            if in_string:
                if c == "\\" :
                    i += 2  # skip escaped char
                    continue
                if c == '"':
                    in_string = False
            else:
                if c == '"':
                    in_string = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(raw[start:i + 1])
                        except json.JSONDecodeError:
                            break
            i += 1

        # JSON was likely truncated by max_tokens — try to repair
        truncated = raw[start:]
        log.warning(f"Attempting truncated JSON repair (len={len(truncated)})")
        # Close any open strings, arrays, objects
        repair = truncated.rstrip(", \n\r\t")
        # Count unclosed braces/brackets
        open_braces = repair.count("{") - repair.count("}")
        open_brackets = repair.count("[") - repair.count("]")
        # Strip trailing incomplete key-value pairs
        if repair.endswith(",") or repair.endswith(":"):
            repair = repair[:-1]
        repair += "]" * max(0, open_brackets)
        repair += "}" * max(0, open_braces)
        try:
            return json.loads(repair)
        except json.JSONDecodeError:
            pass

        log.warning(f"JSON repair failed. Raw (first 300): {raw[:300]}")
        raise ValueError("No complete JSON object found in response")

    def _error_fallback(self, error):
        """Return a standard error result dict."""
        log.error(f"API error: {error}")
        return {
            "objects":    {"detected": False, "list": [], "details": None},
            "structures": {"detected": False, "list": [], "details": None},
            "anomalies":  {"detected": False, "description": None},
            "seabed":     {"visible": False, "type": "unknown"},
            "visibility": "unknown",
            "water_clarity": "unknown",
            "urgency": "none",
            "urgency_reason": "API error",
            "confidence": 0.0,
            "one_line_summary": f"API error: {str(error)[:80]}"
        }
