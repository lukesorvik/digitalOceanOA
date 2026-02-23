from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
	file_id: int
	filename: str
	size_bytes: int
	uploaded_at: datetime


class FileMetadataResponse(BaseModel):
	file_id: int
	filename: str
	content_type: str
	size_bytes: int
	uploaded_at: datetime


class SignedLinkRequest(BaseModel):
	ttl_seconds: int = Field(gt=0, le=86400)


class SignedLinkResponse(BaseModel):
	file_id: int
	ttl_seconds: int
	download_url: str


class LinkAuditResponse(BaseModel):
	audit_id: int
	file_id: int
	filename: str
	requester_user_id: int
	ttl_seconds: int
	created_at: datetime

