from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import database
from app.config import get_settings
from app.routes.download import router as download_router
from app.routes.files import router as files_router


def create_app() -> FastAPI:
	settings = get_settings()
	settings.upload_dir.mkdir(parents=True, exist_ok=True)
	database.init_database(settings.database_url)

	@asynccontextmanager
	async def lifespan(_: FastAPI):
		if database.engine is None:
			database.init_database(settings.database_url)
		database.Base.metadata.create_all(bind=database.engine)
		yield

	app = FastAPI(title=settings.app_name, lifespan=lifespan)

	app.include_router(files_router)
	app.include_router(download_router)

	@app.get("/health")
	def health() -> dict:
		return {"status": "ok"}

	return app


app = create_app()
