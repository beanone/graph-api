"""Main FastAPI application module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from graph_context import BaseGraphContext

from .api.router import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Graph API",
        description="REST API wrapper for graph-context library",
        version="0.1.0",
    )

    # Configure CORS

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure this properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers

    app.include_router(router)

    # Initialize graph context on startup

    @app.on_event("startup")
    async def startup_event():
        app.state.graph_context = BaseGraphContext()

    return app


app = create_app()
