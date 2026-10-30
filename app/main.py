"""Retail Return Reasoning Agent API."""

import logging
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.file_logging import setup_file_logging
from app.core.logging import configure_logging
from app.database.connection import Base, engine
from app.database.session import SessionLocal
from app.models.roles import Role
from app.models.user import User
from app.routers import auth, chat, customer, feedback, investigation, knowledge, product
from app.services.auth import hash_password

return_router = import_module("app.routers.return").router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
	del _app
	configure_logging()
	setup_file_logging()
	Base.metadata.create_all(bind=engine)
	with SessionLocal() as db:
		for role_name in ("administrator", "retail_manager", "analyst", "quality_user"):
			if db.query(Role).filter(Role.role_name == role_name).first() is None:
				db.add(Role(role_name=role_name))
		db.flush()
		admin = db.query(User).filter(User.email == settings.initial_admin_email.lower()).first()
		if admin is None:
			admin_role = db.query(Role).filter(Role.role_name == "administrator").one()
			db.add(User(
				name="Administrator",
				email=settings.initial_admin_email.lower(),
				password_hash=hash_password(settings.initial_admin_password),
				role=admin_role,
			))
			db.commit()
			logger.warning("Created initial administrator account; change its password after first login")
	yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(product.router)
app.include_router(customer.router)
app.include_router(return_router)
app.include_router(feedback.router)
app.include_router(investigation.router)
app.include_router(knowledge.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
	return {"status": "ok"}


# The web page (frontend/index.html) is served at http://127.0.0.1:8000/app/
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
	app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")