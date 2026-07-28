"""FastAPI application entrypoint for the agents service.

Run with:
    uvicorn app:app --reload --port 8000
from this directory.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, status

from api import agent as agent_api
from api.service import agent_service_lifespan, get_agent_service

logger = logging.getLogger(__name__)

def require_internal_token(
    internal_token: str = Header(..., alias="X-Internal-Token"),
) -> None:
    expected = get_agent_service().internal_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_TOKEN is not configured",
        )
    if internal_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal token",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    async with agent_service_lifespan():
        yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agents API",
        version="1.0.0",
        lifespan=lifespan,
        dependencies=[Depends(require_internal_token)],
    )
    app.include_router(agent_api.system_router)
    app.include_router(agent_api.visualizer_router)
    app.include_router(agent_api.feature_extractor_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
