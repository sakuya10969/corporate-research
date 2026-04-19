from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.analysis.router import router as analysis_router
from src.shared.config import get_settings
from src.shared.exceptions import AnalysisError, CollectionError, ExternalServiceError

app = FastAPI(title="企業分析エージェント API", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api")


@app.exception_handler(CollectionError)
async def collection_error_handler(_: Request, exc: CollectionError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(AnalysisError)
async def analysis_error_handler(_: Request, exc: AnalysisError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(ExternalServiceError)
async def external_service_error_handler(_: Request, exc: ExternalServiceError) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})
