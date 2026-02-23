from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()
engine = None
SessionLocal = None


def init_database(database_url: str) -> None:
	global engine, SessionLocal
	connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
	engine = create_engine(database_url, connect_args=connect_args)
	SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
	if SessionLocal is None:
		raise RuntimeError("Database is not initialized")
	session = SessionLocal()
	try:
		yield session
	finally:
		session.close()
