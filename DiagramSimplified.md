flowchart TD
    C[Client: Docs / curl] --> U[POST /files/upload\nx-user-id + file]
    C --> L[GET /files\nx-user-id]
    C --> S[POST /files/id/signed-link\nx-user-id + ttl]
    C --> A[GET /files/users/user_id/link-audits\nx-user-id]
    C --> D[DELETE /files/id\nx-user-id]
    C --> G[GET /download/token\npublic]

    U --> F[(Local File Storage)]
    U --> DB[(Postgres/SQLite metadata)]
    L --> DB
    A --> DB
    D --> DB
    D --> F

    S --> J[Create JWT token\npython-jose + SIGNING_SECRET\nincludes file_id, owner_user_id, exp]
    S --> DB
    J --> G

    G --> V[Verify JWT signature + expiry]
    V --> DB
    V --> F
    G --> R[Return file response]

    subgraph Stack[Core Libraries]
      FA[fastapi + pydantic\nAPI + validation + docs]
      SA[sqlalchemy + psycopg2\nDB ORM + Postgres driver]
      JO[python-jose\nJWT signing/verification]
      MP[python-multipart\nupload parsing]
      UV[uvicorn\nASGI runtime]
    end