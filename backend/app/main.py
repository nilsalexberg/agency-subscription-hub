from fastapi import FastAPI

from app.api.router import api_router
from app.resources import register_admin_resources

app = FastAPI(title="Agency Subscription Hub")

app.include_router(api_router)
register_admin_resources(app)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
