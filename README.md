# HelmetWatch Command Platform

HelmetWatch is a practical starting point for a city-police safety platform that detects likely helmet violations, stores evidence, and surfaces hotspots for follow-up action.

## Important feasibility note

Detecting individual helmet use from true live satellite imagery is generally not realistic because the spatial resolution is too low for reliable per-person safety analysis. This MVP is designed so the same pipeline can ingest:

- traffic camera frames
- drone or aerial feeds
- roadside CCTV
- high-resolution geotagged images

You can still plug in any upstream source labeled as "satellite" later, but the compliance detector should ideally run on higher-resolution imagery.

## What this MVP includes

- FastAPI backend
- SQLite incident store
- upload-based video analysis pipeline
- heuristic detection pipeline with replaceable detector interface
- police dashboard with summary cards, hotspot map, source coverage, and recent incidents
- API endpoints for frame ingest, video ingest, list, pipeline status, and analytics

## Project structure

```text
backend/
  app/
    api/
    services/
    static/
    templates/
media/
  uploads/
```

## Quick start

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the server:

```bash
uvicorn backend.app.main:app --reload
```

4. Open the dashboard:

```text
http://127.0.0.1:8000/
```

## Screenshots

Add your screenshots to the `images/` folder and GitHub will render them here.

### Dashboard

![HelmetWatch Dashboard](images/dashboard.png)

### Upload Workflow

![HelmetWatch Upload Flow](images/upload.png)

## Example ingestion

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "Ward 12 Junction Camera",
    "area_name": "Ward 12",
    "latitude": 25.5941,
    "longitude": 85.1376,
    "captured_at": "2026-04-17T08:30:00",
    "image_url": "https://example.com/frame-001.jpg",
    "vehicle_count": 9
  }'
```

## Example video upload

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze/video \
  -F "media=@sample.mp4" \
  -F "source_name=Ward 12 Drone Patrol" \
  -F "area_name=Ward 12" \
  -F "latitude=25.5941" \
  -F "longitude=85.1376" \
  -F "captured_at=2026-04-17T08:30:00" \
  -F "source_type=drone" \
  -F "sample_every=30"
```

## API overview

- `GET /api/v1/health` basic health check
- `GET /api/v1/pipeline` detector mode and CV availability
- `POST /api/v1/analyze` analyze a single structured frame observation
- `POST /api/v1/analyze/video` upload and sample a video file
- `GET /api/v1/incidents` list incidents
- `GET /api/v1/stats` aggregate dashboard analytics

## Detector upgrade path

The active detector lives in `backend/app/services/detection.py`. Replace the `HeuristicHelmetDetector` with a trained pipeline such as:

- vehicle detector to isolate bikes and scooters
- rider or person detector
- helmet classifier on rider head crops
- confidence thresholding and evidence frame export

The video ingestion flow lives in `backend/app/services/video.py`, so you can later add:

- RTSP ingestion
- scheduled stream polling
- frame buffering
- clip retention for police evidence

## Note on local runs

If you already created `helmetwatch.db` with the older schema, remove it before the first run of this upgraded version so SQLite can recreate the new columns cleanly.

## Next upgrades

- replace the heuristic detector with a real helmet detector
- connect to RTSP/video stream ingestion
- add geofencing and beat-level police assignment
- add evidence review workflow and audit trail
- add anonymization and retention policies
