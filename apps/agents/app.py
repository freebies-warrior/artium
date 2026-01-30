"""FastAPI application entrypoint for the agents service.

Run with:
    uvicorn app:app --reload --port 8000
from this directory.
"""

import logging
from fastapi import FastAPI

from api import agent as agent_api


logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Agents API", version="1.0.0")
    app.include_router(agent_api.router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)