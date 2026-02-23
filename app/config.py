from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class Settings:
	app_name: str
	database_url: str
	upload_dir: Path
	signing_secret: str
	signing_algorithm: str
	max_ttl_seconds: int


def get_settings() -> Settings:
	app_name = os.getenv("APP_NAME", "Private File Service")
	database_url = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
	upload_dir = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
	signing_secret = os.getenv("SIGNING_SECRET", "change-me-in-production")
	signing_algorithm = os.getenv("SIGNING_ALGORITHM", "HS256")
	max_ttl_seconds = int(os.getenv("MAX_TTL_SECONDS", "86400"))

	return Settings(
		app_name=app_name,
		database_url=database_url,
		upload_dir=upload_dir,
		signing_secret=signing_secret,
		signing_algorithm=signing_algorithm,
		max_ttl_seconds=max_ttl_seconds,
	)
