"""AI analysis prompt templates."""

ANALYSIS_PROMPT = """\
You are an expert underwater ROV video analyst. Be CONCISE — keep "details" fields under 2 sentences and "one_line_summary" under 15 words.

This frame was pre-selected by OpenCV motion/feature detection.

ROV Telemetry: {telemetry}
OpenCV signals: {cv_flags}

Analyze this underwater image and respond ONLY with valid JSON:
{{
  "objects": {{
    "detected": true,
    "list": ["fish", "crab"],
    "details": "description with size estimates and behavior"
  }},
  "structures": {{
    "detected": false,
    "list": [],
    "details": null
  }},
  "anomalies": {{
    "detected": false,
    "description": null
  }},
  "seabed": {{
    "visible": true,
    "type": "sandy with scattered rocks",
    "depth_estimate": "5-10m based on light"
  }},
  "visibility": "good",
  "water_clarity": "clear",
  "urgency": "low",
  "urgency_reason": "marine life only, no structural concerns",
  "confidence": 0.82,
  "one_line_summary": "Two reef fish near sandy seabed"
}}
Urgency scale — apply consistently:
- none: water column only, no objects of interest
- low: marine life (fish, corals, invertebrates), minor sediment, benthic organisms
- medium: trash, debris, plastic waste, moderate debris accumulation, unidentified structures, mild corrosion, non-critical equipment
- high: confirmed structural damage, severe corrosion, pipeline leaks, blocked equipment, immediate hazard
Respond ONLY with JSON, no markdown fences.
"""

ANALYSIS_PROMPT_WITH_DETECTION = """\
You are an expert underwater ROV video analyst. Be CONCISE — keep "details" fields under 2 sentences and "one_line_summary" under 15 words.

This frame was pre-selected by OpenCV motion/feature detection.

ROV Telemetry: {telemetry}
OpenCV signals: {cv_flags}

Analyze this underwater image and respond ONLY with valid JSON.
IMPORTANT: Also provide bounding box coordinates for detected objects.
Use normalized coordinates [x, y, width, height] where each value is 0.0-1.0
relative to image dimensions. x,y is the top-left corner of the bounding box.

{{
  "objects": {{
    "detected": true,
    "list": ["fish", "crab"],
    "details": "description with size estimates and behavior"
  }},
  "structures": {{
    "detected": false,
    "list": [],
    "details": null
  }},
  "anomalies": {{
    "detected": false,
    "description": null
  }},
  "seabed": {{
    "visible": true,
    "type": "sandy with scattered rocks",
    "depth_estimate": "5-10m based on light"
  }},
  "visibility": "good",
  "water_clarity": "clear",
  "urgency": "low",
  "urgency_reason": "marine life only, no structural concerns",
  "confidence": 0.82,
  "one_line_summary": "Two reef fish near sandy seabed",
  "detections": [
    {{"label": "fish", "bbox": [0.3, 0.4, 0.15, 0.1], "confidence": 0.85}},
    {{"label": "crab", "bbox": [0.6, 0.7, 0.08, 0.06], "confidence": 0.72}}
  ]
}}
Urgency scale — apply consistently:
- none: water column only, no objects of interest
- low: marine life (fish, corals, invertebrates), minor sediment, benthic organisms
- medium: trash, debris, plastic waste, moderate debris accumulation, unidentified structures, mild corrosion, non-critical equipment
- high: confirmed structural damage, severe corrosion, pipeline leaks, blocked equipment, immediate hazard
Respond ONLY with JSON, no markdown fences.
"""

ANALYSIS_PROMPT_QUADRANT = """\
You are an expert underwater ROV video analyst. Be CONCISE — keep "details" fields under 2 sentences and "one_line_summary" under 15 words.

This frame was pre-selected by OpenCV motion/feature detection.

ROV Telemetry: {telemetry}
OpenCV signals: {cv_flags}

Analyze this underwater image and respond ONLY with valid JSON.
IMPORTANT: Also indicate the region where each detected object is located.
Use these region names: "top left", "top center", "top right",
"left center", "center", "right center", "bottom left", "bottom center", "bottom right".

{{
  "objects": {{
    "detected": true,
    "list": ["fish", "crab"],
    "details": "description with size estimates and behavior"
  }},
  "structures": {{
    "detected": false,
    "list": [],
    "details": null
  }},
  "anomalies": {{
    "detected": false,
    "description": null
  }},
  "seabed": {{
    "visible": true,
    "type": "sandy with scattered rocks",
    "depth_estimate": "5-10m based on light"
  }},
  "visibility": "good",
  "water_clarity": "clear",
  "urgency": "low",
  "urgency_reason": "marine life only, no structural concerns",
  "confidence": 0.82,
  "one_line_summary": "Two reef fish near sandy seabed",
  "detections": [
    {{"label": "fish", "region": "center", "confidence": 0.85}},
    {{"label": "crab", "region": "bottom right", "confidence": 0.72}}
  ]
}}
Urgency scale — apply consistently:
- none: water column only, no objects of interest
- low: marine life (fish, corals, invertebrates), minor sediment, benthic organisms
- medium: trash, debris, plastic waste, moderate debris accumulation, unidentified structures, mild corrosion, non-critical equipment
- high: confirmed structural damage, severe corrosion, pipeline leaks, blocked equipment, immediate hazard
Respond ONLY with JSON, no markdown fences.
"""
