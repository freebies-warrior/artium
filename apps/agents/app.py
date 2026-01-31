"""FastAPI application entrypoint for the agents service.

Run with:
    uvicorn app:app --reload --port 8000
from this directory.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import agent as agent_api
from api.service import agent_service_lifespan

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    async with agent_service_lifespan():
        yield


def create_app() -> FastAPI:
    app = FastAPI(title="Agents API", version="1.0.0", lifespan=lifespan)
    app.include_router(agent_api.system_router)
    app.include_router(agent_api.visualizer_router)
    app.include_router(agent_api.feature_extractor_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
