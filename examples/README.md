# Example Output

This folder contains real example outputs from the ROV AI Analyzer.

## Contents

### Example Job: Video_FHD_camera_image_quality

**Location:** `job_Video_FHD/`

| File | Description |
|------|-------------|
| `frame_00004.jpg` | **Flagged frame** - AI selected this as important |
| `frame_00001.jpg` | Sample extracted frame (start) |
| `frame_00010.jpg` | Sample extracted frame (middle) |
| `frame_00020.jpg` | Sample extracted frame (end) |

### Generated Report

**Location:** `ROV_Reports/`

| File | Description |
|------|-------------|
| `ROV_Report_Video_FHD_camera_image_quality_20260320_230503.pdf` | Full PDF inspection report |

## Example Job Structure

```
ROV_Jobs/
└── Video_FHD_camera_image_quality_20260320_230503/
    ├── job_meta.json              # Full metadata with 42 frames
    ├── all_frames/                # All extracted frames (42 frames)
    │   ├── frame_00001.jpg
    │   └── ...
    └── flagged_frames/            # AI-selected important frames
        ├── frame_00004.jpg       # Sample: sandy seabed with sea pens
        └── ...

ROV_Reports/
└── ROV_Report_Video_FHD_camera_image_quality_20260320_230503.pdf
```

## Sample AI Analysis

See the main README.md for sample AI analysis output based on frame_00004.

---

*Real example data from ROV inspection job.*