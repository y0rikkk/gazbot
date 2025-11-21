"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import time

from app.core.config import settings
from app.core.logging_config import setup_logging

# Настраиваем логирование при старте
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events для FastAPI."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Dev mode: {settings.DEV_MODE}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI app
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

# Configure CORS для Telegram Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Обработчик HTTP исключений (4xx, 5xx)."""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"on {request.method} {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации запросов."""
    logger.warning(
        f"Validation Error on {request.method} {request.url.path}: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


# Middleware для логирования запросов и отлова необработанных ошибок
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование HTTP запросов и обработка исключений."""
    start_time = time.time()

    # Логируем входящий запрос
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Логируем время обработки
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s"
        )

        return response
    except Exception as exc:
        # Логируем необработанное исключение
        process_time = time.time() - start_time
        logger.error(
            f"Unhandled Exception on {request.method} {request.url.path}: {exc} "
            f"- Time: {process_time:.3f}s",
            exc_info=True,
        )

        # Возвращаем 500 ответ
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


@app.get("/")
def root():
    """Root endpoint."""
    logger.debug("Root endpoint called")
    return {"message": "GazBot API", "status": "running"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Подключаем роутеры
from app.routers import users, events, admin, registrations

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(
    registrations.router, prefix="/api/registrations", tags=["registrations"]
)
