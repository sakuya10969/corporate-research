import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.analysis.router import router as analysis_router
from src.auth.router import router as auth_router
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError
from src.shared.llm import init_llm
from src.shared.logger import logger

app = FastAPI(title="企業分析エージェント API", version="0.1.0")

init_llm()

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    logger.info("{} {}", request.method, request.url.path)
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "{} {} → {} ({:.0f}ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.exception_handler(CollectionError)
async def collection_error_handler(_: Request, exc: CollectionError) -> JSONResponse:
    logger.warning("CollectionError: {}", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(AnalysisError)
async def analysis_error_handler(_: Request, exc: AnalysisError) -> JSONResponse:
    logger.error("AnalysisError: {}", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(
    _: Request, exc: ExternalServiceError
) -> JSONResponse:
    logger.error("ExternalServiceError: {}", exc)
    return JSONResponse(status_code=503, content={"detail": str(exc)})
