from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
from contextlib import asynccontextmanager

from web_routes import router as web_router
from api_routes import router as api_router

from repository import TextRepositoryAsync
from services.document_service import DocumentService
from services.summary_generation_service import SummaryGenerationService
from services.llm_text.facade import LLMTextSummaryService
from services.llm_keyword.facade import LLMKeywordService
from services.extraction_text.facade import ExtractionTextSummaryService
from services.extraction_keyword.facade import ExtractionKeywordService
from file_handler import FileUploader
from dependencies import get_document_service, get_uploader

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
UPLOADS_DIR = BASE_DIR / "uploads"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_url = os.environ.get("DB_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'texts_async.db'}")
    repo = TextRepositoryAsync(db_url=db_url)
    await repo.init_models()

    summary_service = SummaryGenerationService(
        llm_text_svc=LLMTextSummaryService(),
        llm_keyword_svc=LLMKeywordService(),
        extraction_text_svc=ExtractionTextSummaryService(),
        extraction_keyword_svc=ExtractionKeywordService(),
    )

    document_service = DocumentService(repo=repo, summary_service=summary_service)
    app.state.document_service = document_service
    app.state.repo = repo
    app.state.uploader = FileUploader(UPLOADS_DIR)

    yield  # тут app работает

    # Shutdown
    if repo := getattr(app.state, "repo", None):
        await repo.engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="Async Document Summary", lifespan=lifespan)

    # Статика и шаблоны
    app.mount("/static", StaticFiles(directory=STATIC_DIR.resolve()), name="static")
    app.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    # Роутеры
    app.include_router(web_router)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
