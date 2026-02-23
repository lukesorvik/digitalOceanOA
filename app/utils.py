from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt


def require_user_id(x_user_id: str | None = Header(default=None)) -> int:
	if x_user_id is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header is required")
	try:
		user_id = int(x_user_id)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-User-Id must be an integer") from exc
	if user_id <= 0:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-User-Id must be positive")
	return user_id


def create_download_token(
	file_id: int,
	owner_user_id: int,
	ttl_seconds: int,
	secret: str,
	algorithm: str,
) -> str:
	expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
	payload = {
		"sub": "file-download",
		"file_id": file_id,
		"owner_user_id": owner_user_id,
		"exp": expires_at,
	}
	return jwt.encode(payload, secret, algorithm=algorithm)


def decode_download_token(token: str, secret: str, algorithm: str) -> dict:
	try:
		payload = jwt.decode(token, secret, algorithms=[algorithm])
	except JWTError as exc:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired download token") from exc

	if payload.get("sub") != "file-download":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token subject")

	return payload
