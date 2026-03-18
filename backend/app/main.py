from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.settings import FRONTEND_DIR
from app.routes.upload import router as upload_router

app = FastAPI()
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)
app.include_router(upload_router)
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")