# 🤖 ROV AI Video Analyzer

Automated underwater ROV inspection analysis using AI vision models. Desktop GUI application with OpenCV frame analysis, multi-provider AI support, and professional PDF report generation.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)
![PySide6](https://img.shields.io/badge/GUI-PySide6_(Qt)-41CD52?style=flat&logo=qt)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-5.0.0-orange)

---

## 📋 About

**ROV (Remotely Operated Vehicle)** inspection is critical for underwater infrastructure — pipelines, offshore platforms, seabed installations need regular monitoring for corrosion, damage, or marine growth.

### Why This Tool?

Traditional ROV inspection involves:
- Recording hours of underwater video 📹
- Manual review (slow, expensive, inconsistent) 👀
- Human fatigue → missed defects ⚠️

This tool **automates** the analysis:
- OpenCV detects motion, edges, and features to extract key frames
- Duplicate frames removed automatically before AI analysis
- AI vision models analyze each unique frame
- Consistent, objective PDF reports for every dive

### Who Is This For?

| User | Use Case |
|------|----------|
| **ROV Operators** | Auto-analyze dive footage on the boat |
| **Inspection Companies** | Scale from 2 inspections/day → 20 |
| **Engineers** | Get PDF reports for integrity assessment |
| **Marine Scientists** | Catalog marine life & habitat conditions |

### Technical Stack

| Component | Technology |
|-----------|------------|
| GUI Framework | PySide6 (Qt for Python) |
| Video Processing | ffmpeg + OpenCV |
| Deduplication | ORB feature matching + histogram + perceptual hash |
| AI Vision | OpenRouter / OpenAI / Anthropic (multi-provider) |
| PDF Generation | fpdf2 (English) |
| Deployment | Windows installer (PyInstaller + Inno Setup) |

---

## ⚡ Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **ffmpeg** on PATH — [download here](https://ffmpeg.org/download.html)
- **Git**

### 2. Install

```bash
git clone https://github.com/ryan354/ROV-Underwater-Video-analysis.git
cd ROV-Underwater-Video-analysis
pip install -r requirements.txt
```

### 3. Run

```bash
python main.py
```

### 4. First-Time Setup

On first launch, press **Ctrl+,** (Settings) and configure:

| Tab | What to set |
|-----|-------------|
| **Folders** | Output folder (for job data) + Reports folder (for PDFs) |
| **AI Config** | Provider, API key, model |
| **Advanced** | Frame interval, dedup threshold |

### 5. Workflow

1. Click **Open Video** → select `.mp4 / .avi / .mkv / .mov`
2. Click **1. Extract & Analyze Frames** — extracts frames, runs OpenCV, removes duplicates
3. Click **2. Run AI Analysis** — AI analyzes each unique frame
4. Click **3. Generate PDF Report** — opens PDF automatically

---

## 🏗️ Pipeline

```
ROV Video
    │
    ▼  ffmpeg (extract 1 frame every N seconds)
All Frames
    │
    ▼  OpenCV (motion / edge / feature / color detection)
Flagged Frames
    │
    ▼  Deduplicator (ORB + histogram + perceptual hash)
Unique Flagged Frames
    │
    ▼  AI Vision (OpenRouter / OpenAI / Anthropic)
Analysis Results (JSON)
    │
    ▼  PDF Generator (fpdf2)
PDF Report
```

---

## ⚙️ Configuration

All settings are in **Settings (Ctrl+,)**. Saved to `config.json`.

### AI Providers

| Provider | Get API Key | Recommended Models |
|----------|-------------|-------------------|
| **OpenRouter** | https://openrouter.ai/ | `google/gemini-2.5-flash-lite` (fast, cheap) |
| **OpenRouter** | same | `google/gemini-2.5-pro-preview` (best quality) |
| **OpenAI** | https://platform.openai.com/ | `gpt-4o`, `gpt-4o-mini` |
| **Anthropic** | https://console.anthropic.com/ | `claude-sonnet-4-20250514` |

### Settings Tabs

| Tab | Options |
|-----|---------|
| **Folders** | Output folder, reports folder |
| **AI Config** | Provider, API key, model, max tokens, object detection mode |
| **OpenCV** | Motion threshold, edge density, feature keypoints, color anomaly ratio |
| **Advanced** | Frame interval (sec), dedup enabled/threshold, verification mode |

### Quick Options (Sidebar)

| Option | Description |
|--------|-------------|
| Frame Interval | Extract 1 frame every N seconds (1–30) |
| Remove duplicates | Toggle ORB/histogram dedup before AI |
| Object detection | AI returns bounding boxes on detected objects |
| Verification mode | Sample only 20 frames for quick testing |

### Dedup Threshold Guide

| Value | Behavior |
|-------|----------|
| `0.3` | Aggressive — removes many similar frames |
| `0.5` | Balanced (default) |
| `0.7` | Moderate — keeps more variation |
| `0.9` | Permissive — only removes near-identical frames |

---

## 📁 Project Structure

```
ROV-Underwater-Video-analysis/
├── main.py                        # Entry point
├── rov_app/
│   ├── app.py                     # QApplication setup
│   ├── core/
│   │   ├── config.py              # ConfigManager (loads config.json)
│   │   ├── constants.py           # Default thresholds
│   │   ├── frame_extractor.py     # ffmpeg wrapper
│   │   ├── opencv_analyzer.py     # OpenCVAnalyzer (motion/edge/feature)
│   │   ├── deduplicator.py        # FrameDeduplicator (ORB + hist + hash)
│   │   ├── telemetry.py           # .srt/.csv/.ass/.vtt parser
│   │   ├── pdf_generator.py       # fpdf2 PDF generation
│   │   ├── annotations.py         # AI detection overlays on frames
│   │   └── job.py                 # job_meta.json CRUD
│   ├── ai/
│   │   ├── base_provider.py       # Abstract AIProvider + JSON parser
│   │   ├── openrouter_provider.py # OpenRouter API
│   │   ├── openai_provider.py     # OpenAI API
│   │   ├── anthropic_provider.py  # Anthropic API
│   │   └── prompt.py              # 3 prompt templates
│   ├── workers/
│   │   ├── extraction_worker.py   # Stage 1 QThread
│   │   ├── analysis_worker.py     # Stage 2 QThread
│   │   └── pdf_worker.py          # PDF QThread
│   └── ui/
│       ├── main_window.py         # Main window (splitter layout)
│       ├── settings_dialog.py     # 4-tab settings dialog
│       ├── frame_grid_widget.py   # Thumbnail grid with urgency colors
│       ├── frame_detail_dialog.py # Full-size frame viewer
│       └── styles.py              # Dark theme QSS
├── config.default.json            # Default configuration
├── config.json                    # User configuration (gitignored)
├── requirements.txt
├── build/
│   ├── rov_app.spec               # PyInstaller spec
│   └── installer.iss              # Inno Setup script
└── examples/                      # Sample outputs
```

---

## 💻 Development with VS Code

### Recommended Extensions

Install these from the Extensions panel (`Ctrl+Shift+X`):

| Extension | Publisher | Why |
|-----------|-----------|-----|
| **Python** | Microsoft | IntelliSense, linting, debugging |
| **Pylance** | Microsoft | Fast type checking and autocomplete |
| **Python Debugger** | Microsoft | Breakpoints in Qt apps |
| **GitLens** | GitKraken | Git blame, history in editor |
| **indent-rainbow** | oderwat | Visual indentation guides |

### Setup Workspace

```bash
# Open project in VS Code
code path/to/ROV-Underwater-Video-analysis
```

Create `.vscode/settings.json` in the project root:

```json
{
  "python.defaultInterpreterPath": "python",
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "dist/": true
  }
}
```

> **Note:** Replace `python.defaultInterpreterPath` with your actual Python/conda env path.
> Find it with: `where python` (Windows) or `which python` (Linux/Mac)

### Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run GUI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "Debug GUI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

Press **F5** to launch with debugger. Set breakpoints by clicking left of line numbers.

### Where to Edit What

| You want to... | Edit this file |
|----------------|---------------|
| Change AI prompt / instructions | `rov_app/ai/prompt.py` |
| Add a new AI provider | `rov_app/ai/` — copy `openrouter_provider.py` |
| Change urgency levels | `rov_app/ai/prompt.py` → urgency scale section |
| Change OpenCV detection logic | `rov_app/core/opencv_analyzer.py` |
| Change dedup algorithm | `rov_app/core/deduplicator.py` |
| Change PDF layout / content | `rov_app/core/pdf_generator.py` |
| Add settings options | `rov_app/ui/settings_dialog.py` + `_save()` method |
| Change main window layout | `rov_app/ui/main_window.py` |
| Change color theme | `rov_app/ui/styles.py` |
| Change default config values | `rov_app/core/constants.py` |
| Add new AI models to dropdown | `rov_app/ui/settings_dialog.py` → `PROVIDER_MODELS` dict |

### Useful VS Code Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+P` | Open file by name (e.g. type `prompt.py`) |
| `Ctrl+Shift+F` | Search across all files |
| `F12` | Go to definition |
| `Shift+F12` | Find all references |
| `Ctrl+\`` | Open terminal |
| `F5` | Run with debugger |
| `Ctrl+F5` | Run without debugger |
| `Ctrl+Shift+P` → "Python: Select Interpreter" | Switch conda env |

### Common Development Tasks

**Run the app:**
```bash
# In VS Code terminal (Ctrl+`)
python main.py
```

**Test a specific module:**
```bash
python -c "from rov_app.core.deduplicator import FrameDeduplicator; print('OK')"
python -c "from rov_app.ai.prompt import ANALYSIS_PROMPT; print(ANALYSIS_PROMPT[:100])"
```

**Check imports are working:**
```bash
python -c "import rov_app; print('All imports OK')"
```

**Watch logs while running:**
The app logs to console. In VS Code terminal you'll see:
```
[INFO]  rov_app.core.frame_extractor: Extracted 57 frames.
[INFO]  rov_app.core.deduplicator: Dedup: 56 -> 45 unique (11 duplicates removed)
[ERROR] rov_app.ai.base_provider: API error: ...
```

---

## 🔧 Troubleshooting

### "No frames extracted"
- Verify ffmpeg is on PATH: `ffmpeg -version`
- Check video file format is `.mp4 / .avi / .mkv / .mov`
- Check output folder is set in Settings

### "API error: No complete JSON object found"
- Increase **Max Tokens** in Settings → AI Config (try 2048–4096)
- Switch to a more capable model (`gemini-2.5-pro-preview`, `gpt-4o`)
- The model may not support JSON output format — try a different provider

### "Read timed out"
- Already fixed — timeout is 120 seconds
- If still timing out, try a faster/lighter model

### "Dedup not removing similar frames"
- Lower the **Dedup Threshold** in Settings → Advanced (try 0.3–0.4)
- Re-run Stage 1 after changing the threshold

### "All frames showing API error"
- Check API key is correct in Settings → AI Config
- Click Show button to verify the key
- Test the key at openrouter.ai/activity

### App won't start
```bash
# Check dependencies
pip install -r requirements.txt

# Check Python version
python --version   # needs 3.10+

# Check PySide6
python -c "from PySide6.QtWidgets import QApplication; print('PySide6 OK')"
```

---

## 🏗️ Building the Windows Installer

The build process produces a single `ROV_Analyzer_v5_Setup.exe` that installs the app on any Windows PC — no Python, no pip, no dependencies needed.

### Distribution Options

| Method | How to share | Target PC experience |
|--------|-------------|----------------------|
| **Setup.exe** (Inno Setup) | Share one `.exe` file | Double-click → wizard → installed with shortcuts + uninstaller |
| **ZIP folder** | Zip `dist\ROV_Analyzer\` | Unzip anywhere → run `ROV_Analyzer.exe` directly |

Both work. Setup.exe is more professional; ZIP is quicker to produce.

---

### What's Bundled

| Included ✅ | Not Included ❌ |
|------------|----------------|
| Python runtime (embedded) | ffmpeg (see below) |
| PySide6 / Qt | |
| OpenCV, numpy | |
| fpdf2, requests | |
| All app code + config | |
| Output & Reports folders (auto-created) | |

---

### One-Time Prerequisites

#### 1. PyInstaller
```bat
pip install pyinstaller
```

#### 2. Inno Setup 6 ✅ (already installed)
Installed at: `C:\Program Files (x86)\Inno Setup 6\`
The build script detects it automatically.

#### 3. ffmpeg on target PCs
The app needs ffmpeg to extract video frames. Pick one option:

**Option A — Users install ffmpeg (simplest):**
1. Download from https://www.gyan.dev/ffmpeg/builds/ → `ffmpeg-release-essentials.zip`
2. Extract to `C:\ffmpeg\`
3. Add `C:\ffmpeg\bin` to Windows PATH
4. Verify: open CMD → `ffmpeg -version`

**Option B — Bundle ffmpeg inside the installer (zero-dependency):**
1. Download `ffmpeg-release-essentials.zip` from https://www.gyan.dev/ffmpeg/builds/
2. Extract `ffmpeg.exe` + `ffprobe.exe` into `build\ffmpeg\`
3. In `build\installer.iss`, uncomment:
   ```ini
   Source: "ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: ignoreversion recursesubdirs
   ```
4. Rebuild — ffmpeg ships inside the installer, no extra steps for users

---

### Build Steps

**Step 1 — Open terminal in project root**
```bat
cd path\to\ROV-Underwater-Video-analysis
```

**Step 2 — Run the build script**
```bat
build\build.bat
```

Output:
```
[1/3] Cleaning previous build...       ← removes old dist\ROV_Analyzer\
[2/3] Building with PyInstaller...     ← bundles Python + all packages
[3/3] Creating installer with Inno Setup...  ← wraps into Setup.exe

DONE  →  dist\ROV_Analyzer_v5_Setup.exe
```

Expected time: **3–8 minutes**

**Step 3 — Test before sharing**
```bat
dist\ROV_Analyzer\ROV_Analyzer.exe
```
Run this directly and verify the app works before distributing.

**Step 4 — Share**

Send `dist\ROV_Analyzer_v5_Setup.exe` (~150–250 MB) to other PCs.

On target PC:
1. Double-click `ROV_Analyzer_v5_Setup.exe`
2. Click **Next → Next → Install**
3. Open from Desktop shortcut or Start Menu
4. Press **Ctrl+,** to configure folders and API key

---

### Quick ZIP Alternative (no Inno Setup needed)

```bat
powershell Compress-Archive -Path "dist\ROV_Analyzer" -DestinationPath "dist\ROV_Analyzer_v5.zip"
```

Share the ZIP → target PC unzips and runs `ROV_Analyzer.exe` directly. No shortcuts or uninstaller, but works immediately.

---

### Build File Reference

| File | Purpose |
|------|---------|
| `build\build.bat` | One-click build script |
| `build\rov_app.spec` | PyInstaller config (imports, data files) |
| `build\installer.iss` | Inno Setup config (shortcuts, PATH, folders) |
| `dist\ROV_Analyzer\` | Standalone app folder (PyInstaller output) |
| `dist\ROV_Analyzer_v5_Setup.exe` | Windows installer to distribute |

---

### Build Troubleshooting

**`ERROR: script '...\main.py' not found`**
- Run `build\build.bat` from the **project root**, not from inside `build\`
- Run `build\build.bat` from the project root directory

**`PyInstaller not found`**
```bat
pip install pyinstaller
```

**`Inno Setup not found`**
- Already installed — check it's at `C:\Program Files (x86)\Inno Setup 6\ISCC.exe`
- Or run manually: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss`

**App crashes on target PC — "DLL not found"**
- Install [Visual C++ Redistributable x64](https://aka.ms/vs/17/release/vc_redist.x64.exe) on the target PC

**App opens but video won't process — "ffmpeg not found"**
- Install ffmpeg on the target PC (Option A) or rebuild with bundled ffmpeg (Option B)

**App takes 5–10 seconds to open**
- Normal for PyInstaller apps on first launch — it extracts files to a temp folder

---

## 📊 Output Example

After running, job folders look like:

```
Output/
└── video_name_20260328_102345/
    ├── job_meta.json          # All job state (used by Stage 2)
    ├── all_frames/            # All extracted frames
    │   ├── frame_00001.jpg
    │   └── ...
    └── flagged_frames/        # OpenCV-selected + deduped frames
        ├── frame_00003.jpg
        └── ...

Reports/
└── ROV_Report_video_name_20260328_102345.pdf
```

---

## ❓ FAQ

**Q: What video formats are supported?**
`.mp4`, `.avi`, `.mkv`, `.mov`

**Q: How does frame selection work?**
OpenCV checks each frame for: motion (frame diff), edge density (Canny), feature richness (ORB keypoints), color anomalies (unusual hue ratios). Frames passing any threshold are flagged.

**Q: How much does AI analysis cost?**
~$0.001–0.005 per frame. A 10-min video @ 5 sec = ~120 frames → ~$0.12–0.60 per job with Gemini Flash.

**Q: Can I run without GPU?**
Yes — OpenCV runs on CPU. AI calls are API-based (remote).

**Q: How do I add a new model?**
Open `rov_app/ui/settings_dialog.py`, find `PROVIDER_MODELS`, add the model string to the relevant provider list.

**Q: Can I customize the AI prompt?**
Yes — edit `rov_app/ai/prompt.py`. The urgency scale, output fields, and instructions are all there.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first.

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

- **ryaan**
- GitHub: [ryan354](https://github.com/ryan354)
- Email: ryaan354@gmail.com

---

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) — multi-model AI API
- [Google Gemini](https://deepmind.google/technologies/gemini/) — primary vision model
- [fpdf2](https://pyfpdf.github.io/fpdf2/) — PDF generation
- [OpenCV](https://opencv.org/) — video frame analysis
- [PySide6](https://doc.qt.io/qtforpython/) — Qt GUI framework
