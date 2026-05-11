import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import (
    auth,
    conversations,
    deliveries,
    health,
    messages,
    users,
    websocket,
)
from app.core.config import settings
from app.websocket.pubsub_listener import start_pubsub_listener


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(deliveries.router)
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_pubsub_listener())


@app.get("/")
async def root():
    return {
        "message": "Ahoy captain, chat backend is sailing!",
        "environment": settings.APP_ENV,
    }