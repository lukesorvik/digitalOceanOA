flowchart TD
    Client[Client: Swagger UI / curl] --> Health[GET /health]
    Client --> Upload[POST /files/upload<br/>Header: X-User-Id<br/>multipart file]
    Client --> ListFiles["GET /files<br/>Header: X-User-Id"]
    Client --> SignLink["POST /files/:file_id/signed-link<br/>Header: X-User-Id<br/>Body: ttl_seconds"]
    Client --> ListAudits["GET /files/users/:user_id/link-audits<br/>Header: X-User-Id"]
    Client --> DeleteFile["DELETE /files/:file_id<br/>Header: X-User-Id"]
    Client --> Download["GET /download/:token<br/>Public"]

    subgraph App ["FastAPI App"]
        Health --> FastAPI[FastAPI Router Layer]
        Upload --> FastAPI
        ListFiles --> FastAPI
        SignLink --> FastAPI
        ListAudits --> FastAPI
        DeleteFile --> FastAPI
        Download --> FastAPI
    end

    FastAPI --> AuthDep[require_user_id dependency<br/>validates X-User-Id]

    Upload --> Multipart[python-multipart parses upload]
    Upload --> FSWrite[Write file to UPLOAD_DIR<br/>private local storage]
    Upload --> ORMCreateFile[SQLAlchemy insert StoredFile]

    ListFiles --> ORMListFiles[SQLAlchemy query StoredFile by owner]

    SignLink --> ORMFindFile[SQLAlchemy find owner file]
    SignLink --> JWTEncode[python-jose jwt.encode<br/>HS256 + SIGNING_SECRET<br/>claims: file_id, owner_user_id, exp]
    SignLink --> ORMAuditCreate[SQLAlchemy insert LinkAudit<br/>who, file, ttl]
    SignLink --> URLBuild[Build download URL<br/>respect forwarded host/proto]

    ListAudits --> Authz[Authorize path user_id equals header user]
    ListAudits --> ORMListAudits[SQLAlchemy join LinkAudit + StoredFile]

    DeleteFile --> ORMFindDelete[SQLAlchemy find owner file]
    DeleteFile --> FSDelete[Delete physical file if exists]
    DeleteFile --> ORMAuditDelete[Delete link audits for file]
    DeleteFile --> ORMDeleteFile[Delete StoredFile row]

    Download --> JWTDecode[python-jose jwt.decode<br/>verify signature + exp + subject]
    Download --> ORMVerifyFile[SQLAlchemy query StoredFile by token claims]
    Download --> FSRead[Read file from upload_path]
    Download --> FileResp[FastAPI FileResponse stream file]

    subgraph Data ["Persistence"]
        DB[(PostgreSQL / SQLite)]
        Disk[(Local File System)]
    end

    ORMCreateFile --> DB
    ORMListFiles --> DB
    ORMFindFile --> DB
    ORMAuditCreate --> DB
    ORMListAudits --> DB
    ORMFindDelete --> DB
    ORMAuditDelete --> DB
    ORMDeleteFile --> DB
    ORMVerifyFile --> DB

    FSWrite --> Disk
    FSDelete --> Disk
    FSRead --> Disk

    subgraph Runtime ["Container and Runtime"]
        Docker[Docker image<br/>Python 3.12 + dependencies]
        Uvicorn[Uvicorn ASGI server<br/>--proxy-headers]
        DO[DigitalOcean App Platform]
    end

    Docker --> Uvicorn --> FastAPI
    DO --> Uvicorn

    subgraph Libs ["Libraries Used"]
        L1[fastapi<br/>Routing, validation, docs]
        L2[uvicorn<br/>ASGI server]
        L3[sqlalchemy<br/>ORM and DB access]
        L4[psycopg2-binary<br/>Postgres driver]
        L5[python-jose<br/>JWT sign/verify]
        L6[python-multipart<br/>File upload parsing]
        L7[pydantic<br/>Schemas and serialization]
        L8[pytest + TestClient<br/>Automated API tests]
    end

    L1 --> FastAPI
    L2 --> Uvicorn
    L3 --> ORMCreateFile
    L3 --> ORMListFiles
    L3 --> ORMFindFile
    L3 --> ORMAuditCreate
    L3 --> ORMListAudits
    L3 --> ORMFindDelete
    L3 --> ORMAuditDelete
    L3 --> ORMDeleteFile
    L3 --> ORMVerifyFile
    L4 --> DB
    L5 --> JWTEncode
    L5 --> JWTDecode
    L6 --> Multipart
    L7 --> FastAPI
    L8 --> Client