# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

Requires **ffmpeg** on PATH (used via subprocess for frame extraction).

## Commands

```bash
# Launch GUI application
python main.py
python -m rov_app

# Legacy CLI (still works)
python rov_watcher.py path/to/video.mp4
python rov_analyzer.py path/to/job_folder

# Build installer
pip install pyinstaller
pyinstaller build/rov_app.spec
```

No test suite exists yet.

## Architecture

PySide6 desktop GUI with a two-stage pipeline:

```
Video → Stage 1 (ffmpeg + OpenCV + Dedup) → [GUI approval] → Stage 2 (AI analysis) → PDF Report
```

### Package Structure

- **`rov_app/core/`** — Pure logic modules (no GUI dependency):
  - `opencv_analyzer.py` — `OpenCVAnalyzer` class (stateful, keeps `prev_gray` for motion detection). Constructor accepts threshold dict.
  - `frame_extractor.py` — wraps ffmpeg subprocess, accepts `on_progress` callback
  - `deduplicator.py` — ORB feature matching to remove near-duplicate flagged frames
  - `telemetry.py` — parses `.srt`, `.csv`, `.ass`, `.vtt` subtitle formats for ROV sensor data
  - `pdf_generator.py` — fpdf2 report generation (English), optional AI detection overlays
  - `annotations.py` — draws OpenCV flags and AI bounding boxes/quadrant highlights on frames
  - `config.py` — `ConfigManager` loads/saves `config.json`, falls back to `.env`
  - `job.py` — job_meta.json CRUD, job directory management
  - `constants.py` — default thresholds, supported extensions

- **`rov_app/ai/`** — Multi-provider AI abstraction:
  - `base_provider.py` — abstract `AIProvider` with shared prompt building and JSON parsing
  - `openrouter_provider.py`, `openai_provider.py`, `anthropic_provider.py` — all use raw `requests`
  - `prompt.py` — 3 prompt templates: basic, precise detection (bbox), quadrant detection (region names)

- **`rov_app/workers/`** — QThread workers for non-blocking operations:
  - `extraction_worker.py` — Stage 1: ffmpeg + OpenCV + dedup, emits per-frame signals
  - `analysis_worker.py` — Stage 2: AI loop with per-frame progress
  - `pdf_worker.py` — PDF generation in background thread

- **`rov_app/ui/`** — PySide6 GUI:
  - `main_window.py` — splitter layout: left sidebar (controls/history) + center (frame grid + analysis)
  - `settings_dialog.py` — 4-tab dialog (Folders, AI, OpenCV, Advanced)
  - `frame_grid_widget.py` — scrollable thumbnail grid with color-coded borders by urgency
  - `frame_detail_dialog.py` — full-size frame view with all analysis data
  - `styles.py` — dark theme QSS (Catppuccin Mocha palette)

### Inter-stage Contract

`job_meta.json` in each job folder contains all state: `stage1_results`, `flagged_list`, telemetry, paths, status. Stage 2 can run independently on any job folder.

## Key Design Details

- **OpenCV thresholds** are configurable via `config.json` and the Settings dialog. Defaults in `core/constants.py`.
- **Deduplication** uses ORB descriptors + BFMatcher with Lowe's ratio test. Threshold configurable (default 0.7).
- **AI detection modes**: "precise" (normalized bbox coords) or "quadrant" (region names). Selected in Settings.
- **PDF reports** are generated in English.
- **All long operations** run in QThread workers. GUI communicates via Qt signals only — no shared mutable state.
- **Config precedence**: `config.default.json` < `.env` < `config.json` (user overrides).

## External Services

| Service | Purpose | Config Key |
|---------|---------|------------|
| OpenRouter API | Multi-model AI vision (Gemini, Claude, GPT) | `ai.api_key` + `ai.provider` |
| OpenAI API | GPT-4o vision | `ai.api_key` + `ai.provider` |
| Anthropic API | Claude vision | `ai.api_key` + `ai.provider` |
| ffmpeg | Frame extraction from video files | Must be on PATH |
