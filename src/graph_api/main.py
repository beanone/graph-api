"""Main FastAPI application module."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from graph_context import BaseGraphContext

from .api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph_context = BaseGraphContext()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="Graph API",
        description="REST API wrapper for graph-context library",
        version="0.1.0",
        lifespan=lifespan,
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

    # Add exception handler

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions.

        Args:
            request: The request
            exc: The exception

        Returns:
            JSONResponse: The error response
        """
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    return app


app = create_app()
