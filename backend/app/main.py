from fastapi import FastAPI

from app.api.router import api_router

app = FastAPI(title="Agency Subscription Hub")

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
