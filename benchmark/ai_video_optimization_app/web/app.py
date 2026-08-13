"""FastAPI application factory for MotionForge."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from orchestrator.config import AppConfig, load_config, setup_logging
from orchestrator.engine import Engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    Initializes configuration, logging, and the orchestration engine
    on startup.
    """
    config: AppConfig = load_config()
    setup_logging(config.log_level)
    engine = Engine(config)

    app.state.config = config
    app.state.engine = engine
    logger.info("MotionForge application started")
    yield
    logger.info("MotionForge application shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(title="MotionForge", lifespan=lifespan)

    # Static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Templates
    templates_dir = Path(__file__).parent / "templates"
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # Register routes
    from web.routes import router  # noqa: F401

    app.include_router(router)

    return app


def main() -> None:
    """Entry point for running the application with uvicorn."""
    import uvicorn

    config = load_config()
    setup_logging(config.log_level)
    uvicorn.run(
        "web.app:create_app",
        factory=True,
        host=config.server.host,
        port=config.server.port,
    )


if __name__ == "__main__":
    main()
