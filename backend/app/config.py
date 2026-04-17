from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'helmetwatch.db'}"
MEDIA_ROOT = PROJECT_ROOT / "media"
UPLOADS_DIR = MEDIA_ROOT / "uploads"
SAMPLES_DIR = MEDIA_ROOT / "samples"
