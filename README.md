# 🤖 ROV AI Video Analyzer

Automated underwater ROV inspection analysis using AI vision models. Detects defects, generates PDF reports, and sends to Telegram for approval.

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-1.0.0-orange)

---

## 📸 Overview

This tool automates ROV (Remotely Operated Vehicle) underwater video inspection:

```
📹 ROV Video → 🎞️ Extract Frames → 🧠 AI Analysis → 📊 PDF Report → 📱 Telegram Approval
```

### What It Does

| Feature | Description |
|---------|-------------|
| **Auto-Detection** | Watches folder for new videos automatically |
| **AI Vision** | Uses Gemini/Claude for frame analysis |
| **PDF Reports** | Generates professional inspection reports |
| **Telegram Bot** | Sends notifications and reports for approval |
| **Motion Detection** | Skips boring static frames |

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  ROV Camera     │    │  This Tool       │    │  AI Service     │
│  Records Video  │───▶│  1. Watch        │───▶│  (OpenRouter)   │
│                 │    │  2. Extract      │    │  Gemini/Claude  │
│  D:\ROV_Videos  │    │  3. Analyze      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Output          │
                        │  • D:\ROV_Jobs   │
                        │  • PDF Report    │
                        │  • Telegram      │
                        └──────────────────┘
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.8+
- OpenRouter API key (free tier available)
- Telegram Bot Token (optional)

### 5-Minute Setup

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/rov-ai-analyzer.git
cd rov-ai-analyzer

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
copy .env.example .env
# Edit .env with your settings (see below)

# 5. Run!
python rov_watcher.py
```

That's it! 🎉

---

## ⚙️ Configuration

### Step 1: Get API Keys

**OpenRouter API Key** (for AI analysis)
1. Go to https://openrouter.ai/
2. Sign up and get free API key
3. Recommended model: `google/gemini-2.5-flash-lite` (fast & cheap)

**Telegram Bot** (for notifications)
1. Message @BotFather on Telegram
2. Send `/newbot` and follow instructions
3. Save your bot token
4. Start a chat with your bot
5. Get your Chat ID: https://t.me/userinfobot

### Step 2: Edit `.env` File

```env
# ===========================================
# REQUIRED - AI & Telegram
# ===========================================
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=8663570805

# ===========================================
# FOLDERS - Adjust to your setup
# ===========================================
WATCH_FOLDER=D:\ROV_Videos      # Where ROV videos are saved
OUTPUT_FOLDER=D:\ROV_Jobs       # Where to save processed jobs
REPORTS_FOLDER=D:\ROV_Reports  # Where to save PDF reports

# ===========================================
# AI MODEL (usually don't need to change)
# ===========================================
MODEL_ID=google/gemini-2.5-flash-lite

# ===========================================
# OPTIONS
# ===========================================
FRAME_EVERY_SEC=5              # Extract frame every X seconds
VERIFICATION_MODE=false        # true = only 5 frames (testing)
APPROVAL_TIMEOUT_SEC=600      # 10 minutes for telegram approval
```

---

## 📖 Usage

### Mode 1: Watch Mode (Recommended)

Monitors your video folder automatically. Runs 24/7.

```bash
python rov_watcher.py
```

**What happens:**
1. Detects new video in `WATCH_FOLDER`
2. Extracts frames (every 5 seconds by default)
3. Saves to `OUTPUT_FOLDER/job_name/frames/`
4. Creates `job_meta.json`
5. Runs AI analysis
6. Generates PDF report
7. Sends to Telegram

### Mode 2: Manual Analysis

Analyze a specific job folder.

```bash
# Analyze latest job
python rov_analyzer.py

# Analyze specific job
python rov_analyzer.py D:\ROV_Jobs\my_job_20240315
```

### Mode 3: Test Mode

Run with only 5 frames to test setup.

```bash
VERIFICATION_MODE=true python rov_analyzer.py
```

---

## 📁 Project Structure

```
rov-ai-analyzer/
├── rov_watcher.py         # Folder watcher - auto-detect videos
├── rov_analyzer.py        # AI analyzer - process frames
├── requirements.txt       # Python dependencies
├── .env.example           # Configuration template
├── examples/              # Example outputs
│   ├── job_output/        # Sample job data
│   └── README.md          # Example documentation
├── README.md              # This file
├── CONTRIBUTING.md        # How to contribute
├── .gitignore             # Git ignore patterns
└── LICENSE                # MIT License
```

---

## 📊 Example Output

See the `examples/` folder for sample outputs.

### Input → Output Flow

| Step | Description | Example |
|------|-------------|---------|
| 1. Video | ROV records video | `video.mp4` (500MB) |
| 2. Frames | Extract every 5 seconds | 50 frames extracted |
| 3. Metadata | Save job info | `job_meta.json` |
| 4. Analysis | AI processes frames | `sample_analysis.txt` |
| 5. Report | Generate PDF | `job_report.pdf` |

### Sample Job Structure

After running, you'll get:

```
ROV_Jobs/
└── 20260115_143022_sample/
    ├── job_meta.json          # Processing info
    ├── all_frames/            # All extracted frames
    │   ├── frame_00001.jpg
    │   └── frame_00002.jpg
    └── flagged_frames/        # Important frames (AI selected)
        ├── frame_00001.jpg
        └── frame_00004.jpg

ROV_Reports/
└── 20260115_143022_sample_report.pdf  # Final report
```

### Sample AI Analysis

```
Frame: frame_00001.jpg (00:00:00)
================================
Condition: ACCEPTABLE

Analysis:
- Clear underwater visibility (8-10m)
- Metal pipeline structure visible
- No corrosion or damage detected
- Light marine growth (~15% coverage)

Recommendation: Continue standard monitoring
```

---

## 🔧 Troubleshooting

### "No frames extracted"
- Check video file is in correct format (.mp4, .avi, .mkv, .mov)
- Verify `WATCH_FOLDER` path exists

### "API key not working"
- Make sure `OPENROUTER_API_KEY` is set in `.env`
- Check you have credits at openrouter.ai

### "Telegram not sending"
- Verify bot token is correct
- Make sure you've started a chat with your bot
- Check `TELEGRAM_CHAT_ID` is numeric

### "Permission denied"
- On Windows, run as Administrator
- Check folder write permissions

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 👤 Author

- Your Name
- GitHub: [yourusername](https://github.com/yourusername)
- Email: you@example.com

---

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) - AI API
- [FPDF](https://pyfpdf.github.io/fpdf2/) - PDF generation
- [OpenCV](https://opencv.org/) - Video processing
