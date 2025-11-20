"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Configure CORS для Telegram Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "GazBot API", "status": "running"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Подключаем роутеры
from app.routers import users, events

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
