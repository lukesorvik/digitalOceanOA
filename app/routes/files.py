from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import LinkAudit, StoredFile
from app.schemas import FileMetadataResponse, SignedLinkRequest, SignedLinkResponse, UploadResponse
from app.utils import create_download_token, require_user_id


router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
	file: UploadFile = File(...),
	user_id: int = Depends(require_user_id),
	db: Session = Depends(get_db),
):
	settings = get_settings()
	upload_dir = settings.upload_dir
	upload_dir.mkdir(parents=True, exist_ok=True)

	original_name = file.filename or "unnamed"
	stored_filename = f"{uuid.uuid4().hex}_{Path(original_name).name}"
	destination = upload_dir / stored_filename

	bytes_written = 0
	with destination.open("wb") as out_file:
		while True:
			chunk = await file.read(1024 * 1024)
			if not chunk:
				break
			out_file.write(chunk)
			bytes_written += len(chunk)

	db_file = StoredFile(
		owner_user_id=user_id,
		original_filename=original_name,
		stored_filename=stored_filename,
		content_type=file.content_type or "application/octet-stream",
		size_bytes=bytes_written,
		upload_path=str(destination),
	)
	db.add(db_file)
	db.commit()
	db.refresh(db_file)

	return UploadResponse(
		file_id=db_file.id,
		filename=db_file.original_filename,
		size_bytes=db_file.size_bytes,
		uploaded_at=db_file.created_at,
	)


@router.get("", response_model=list[FileMetadataResponse])
def list_user_files(
	user_id: int = Depends(require_user_id),
	db: Session = Depends(get_db),
):
	files = (
		db.query(StoredFile)
		.filter(StoredFile.owner_user_id == user_id)
		.order_by(StoredFile.created_at.desc())
		.all()
	)
	return [
		FileMetadataResponse(
			file_id=stored_file.id,
			filename=stored_file.original_filename,
			content_type=stored_file.content_type,
			size_bytes=stored_file.size_bytes,
			uploaded_at=stored_file.created_at,
		)
		for stored_file in files
	]


@router.post("/{file_id}/signed-link", response_model=SignedLinkResponse)
def create_signed_link(
	file_id: int,
	payload: SignedLinkRequest,
	request: Request,
	user_id: int = Depends(require_user_id),
	db: Session = Depends(get_db),
):
	settings = get_settings()

	if payload.ttl_seconds > settings.max_ttl_seconds:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail=f"ttl_seconds exceeds max allowed value ({settings.max_ttl_seconds})",
		)

	stored_file = (
		db.query(StoredFile)
		.filter(StoredFile.id == file_id, StoredFile.owner_user_id == user_id)
		.first()
	)
	if stored_file is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

	token = create_download_token(
		file_id=stored_file.id,
		owner_user_id=stored_file.owner_user_id,
		ttl_seconds=payload.ttl_seconds,
		secret=settings.signing_secret,
		algorithm=settings.signing_algorithm,
	)

	audit = LinkAudit(file_id=stored_file.id, requester_user_id=user_id, ttl_seconds=payload.ttl_seconds)
	db.add(audit)
	db.commit()

	forwarded_proto = request.headers.get("x-forwarded-proto")
	forwarded_host = request.headers.get("x-forwarded-host")
	host = forwarded_host or request.headers.get("host")
	scheme = forwarded_proto or request.url.scheme

	if host:
		download_url = f"{scheme}://{host}/download/{token}"
	else:
		download_url = f"{str(request.base_url).rstrip('/')}/download/{token}"

	return SignedLinkResponse(file_id=stored_file.id, ttl_seconds=payload.ttl_seconds, download_url=download_url)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
	file_id: int,
	user_id: int = Depends(require_user_id),
	db: Session = Depends(get_db),
):
	stored_file = (
		db.query(StoredFile)
		.filter(StoredFile.id == file_id, StoredFile.owner_user_id == user_id)
		.first()
	)
	if stored_file is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

	file_path = Path(stored_file.upload_path)
	if file_path.exists() and file_path.is_file():
		file_path.unlink()

	db.query(LinkAudit).filter(LinkAudit.file_id == stored_file.id).delete(synchronize_session=False)
	db.delete(stored_file)
	db.commit()
