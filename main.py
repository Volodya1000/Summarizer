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
#from services.llm_text.llm_text_summary_service import  LLMTextSummaryService

from services.extraction_text.facade import ExtractionTextSummaryService



from services.extraction_keyword.facade import ExtractionKeywordService
from services.translator import LocalTranslator

from services.llm_keyword.facade import LLMKeywordService
#from services.llm_keyword.keyword_tree_generator_llm import LLMKeywordService

from services.ollama_client import OllamaClient

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

    ollama_client = OllamaClient(model_name="gpt-oss:120b-cloud")
    #llm_keyword_svc=LLMKeywordService(client=ollama_client)
    llm_keyword_svc=LLMKeywordService()

    #llm_text_svc=LLMTextSummaryService(client=ollama_client)
    llm_text_svc=LLMTextSummaryService()

    summary_service = SummaryGenerationService(
        llm_text_svc=llm_text_svc,
        llm_keyword_svc=llm_keyword_svc,
        extraction_text_svc=ExtractionTextSummaryService(summary_size=10),
        extraction_keyword_svc=ExtractionKeywordService(LocalTranslator()),
    )

    document_service = DocumentService(repo=repo, summary_service=summary_service)
    app.state.document_service = document_service
    app.state.repo = repo
    app.state.uploader = FileUploader(UPLOADS_DIR)

    yield  
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # обязательно выключить reload для отладки
        log_level="debug",
    )
