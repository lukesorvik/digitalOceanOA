# Private File Service (FastAPI)

REST API service for private file uploads with temporary, cryptographically signed download links.

## Features

- Upload private files to a non-public local directory.
- Associate each file with an owner user ID (`X-User-Id` header).
- Generate signed download URLs with configurable TTL.
- Validate signatures and expiry on public download endpoint.
- List owner file metadata (filename, size, upload date).
- Audit every signed-link generation event.

## Quick Start

### 1) Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies


```bash
pip install -r requirements.txt
```

### 3) Run the API

```bash
uvicorn app.main:app --reload
```

API docs are available at:

- `http://127.0.0.1:8000/docs`

## Testing via docs
In FastAPI docs (/docs), for each protected endpoint:

Click Try it out
Find header param x-user-id
Enter an integer like 1
Then click Execute

### or via terminal 
Upload (with owner): curl -X POST "$BASE/files/upload" -H "X-User-Id: 1" -F "file=@./sample.txt"
List files: curl "$BASE/files" -H "X-User-Id: 1"
Create signed link: curl -X POST "$BASE/files/<file_id>/signed-link" -H "X-User-Id: 1" -H "Content-Type: application/json" -d '{"ttl_seconds":600}'
Download via returned URL: curl -L "<download_url>" -o downloaded.txt

## Configuration

Environment variables:

- `APP_NAME` (default: `Private File Service`)
- `DATABASE_URL` (default: `sqlite:///./data/app.db`)
- `UPLOAD_DIR` (default: `data/uploads`)
- `SIGNING_SECRET` (default: `change-me-in-production`)
- `SIGNING_ALGORITHM` (default: `HS256`)
- `MAX_TTL_SECONDS` (default: `86400`)

Example:

```bash
export SIGNING_SECRET="super-long-random-secret"
export DATABASE_URL="sqlite:///./data/app.db"
```

## API Endpoints

### Health

- `GET /health`

### Upload file (private)

- `POST /files/upload`
- Header: `X-User-Id: <integer>`
- Form field: `file` (multipart)

### List owner files (metadata)

- `GET /files`
- Header: `X-User-Id: <integer>`

### Generate signed link

- `POST /files/{file_id}/signed-link`
- Header: `X-User-Id: <integer>`
- JSON body:

```json
{
	"ttl_seconds": 600
}
```

### Download file by signed URL (public)

- `GET /download/{token}`

## Tests

Run:

```bash
pytest -q
```

## Run with Docker

### Build image

```bash
docker build -t private-file-api:latest .
```

### Run container

```bash
docker run --rm -p 8000:8000 \
	-e SIGNING_SECRET="replace-with-a-strong-secret" \
	-e DATABASE_URL="sqlite:////app/data/app.db" \
	-e UPLOAD_DIR="/app/data/uploads" \
	-v "$(pwd)/data:/app/data" \
	private-file-api:latest
```

## Run with Docker Compose

```bash
docker compose up --build -d
```

Stop:

```bash
docker compose down
```

## CI

GitHub Actions workflow is included at `.github/workflows/ci.yml` and runs tests on push and pull request.

## Deploying to DigitalOcean (App Platform)

1. Push this repo to your GitHub account.
2. In DigitalOcean, create a new App from GitHub source.
3. Select Dockerfile-based deploy (App Platform detects `Dockerfile`).
4. Set runtime environment variables:
	- `SIGNING_SECRET`
	- `DATABASE_URL` (for production, prefer managed Postgres)
	- `UPLOAD_DIR`
	- `MAX_TTL_SECONDS`
5. For persistent file storage, mount a volume or migrate uploads to object storage.
6. Deploy and validate `GET /health` and signed-link flow.

Production note: local filesystem upload storage works for single-instance setups. For horizontal scaling, use object storage (for example DigitalOcean Spaces) and keep signing keys in a secret manager.