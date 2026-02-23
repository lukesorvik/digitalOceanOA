from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import StoredFile
from app.utils import decode_download_token


router = APIRouter(tags=["download"])


@router.get("/download/{token}")
def download_file(token: str, db: Session = Depends(get_db)):
	settings = get_settings()
	payload = decode_download_token(token, settings.signing_secret, settings.signing_algorithm)

	file_id = payload.get("file_id")
	owner_user_id = payload.get("owner_user_id")
	if not isinstance(file_id, int) or not isinstance(owner_user_id, int):
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Malformed token")

	stored_file = (
		db.query(StoredFile)
		.filter(StoredFile.id == file_id, StoredFile.owner_user_id == owner_user_id)
		.first()
	)
	if stored_file is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

	path = Path(stored_file.upload_path)
	if not path.exists():
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File data missing")

	return FileResponse(
		path=path,
		media_type=stored_file.content_type,
		filename=stored_file.original_filename,
	)
