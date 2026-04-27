import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .logging_config import (
    new_request_id,
    request_id_var,
    setup_logging,
    user_id_var,
)
from .routers import generate, personas, samples
from .vectorstore import ensure_index

setup_logging()
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup")
    ensure_index()
    yield
    log.info("shutdown")


app = FastAPI(title="Write2Style API", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    rid_token = request_id_var.set(rid)
    user_token = user_id_var.set("-")
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.exception(
            "request_failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
        )
        raise
    else:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["x-request-id"] = rid
        return response
    finally:
        request_id_var.reset(rid_token)
        user_id_var.reset(user_token)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code >= 500:
        log.error(
            "http_exception",
            extra={"status": exc.status_code, "detail": str(exc.detail)},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": request_id_var.get()},
        headers={"x-request-id": request_id_var.get()},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning("validation_error", extra={"errors": exc.errors()})
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": request_id_var.get(),
        },
        headers={"x-request-id": request_id_var.get()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id_var.get(),
        },
        headers={"x-request-id": request_id_var.get()},
    )


app.include_router(personas.router)
app.include_router(samples.router)
app.include_router(generate.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
