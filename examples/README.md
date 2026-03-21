# Example Output

This folder contains real example outputs from the ROV AI Analyzer.

## Contents

### Example Job: Video_FHD_camera_image_quality

**Location:** `job_Video_FHD/`

| File | Description |
|------|-------------|
| `ROV_Report_...pdf` | Generated PDF inspection report |
| `frame_00001.jpg` | Sample extracted frame (start) |
| `frame_00010.jpg` | Sample extracted frame (middle) |
| `frame_00020.jpg` | Sample extracted frame (end) |

## Example Job Structure

```
ROV_Jobs/
└── Video_FHD_camera_image_quality_20260320_230503/
    ├── job_meta.json              # Full metadata with 20+ frames
    ├── all_frames/                # All extracted frames (20 frames)
    │   ├── frame_00001.jpg
    │   ├── frame_00002.jpg
    │   └── ...
    └── flagged_frames/            # AI-selected important frames

ROV_Reports/
└── ROV_Report_Video_FHD_camera_image_quality_20260320_230503.pdf
```

## Sample PDF Report

The PDF contains:
- Job information (date, duration, frame count)
- Per-frame AI analysis
- Condition assessment (Good/Acceptable/Poor)
- Specific observations
- Recommendations

## Workflow Summary

1. **Video Input** → ROV records video
2. **Watcher Detects** → Auto-detects new video
3. **Frame Extraction** → Extracts frames every N seconds
4. **AI Analysis** → Sends frames to AI vision model
5. **PDF Report** → Generates professional inspection report
6. **Telegram** → Sends notification for approval

---

*Real example data from ROV inspection job.*