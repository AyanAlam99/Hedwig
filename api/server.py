import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.engine import pc_background_loop
from core.state import ui_log
from api.routers import setup, logs

@asynccontextmanager
async def lifespan(app: FastAPI):
    ui_log("Starting Hedwig Backend...", "sys")
    threading.Thread(target=pc_background_loop, daemon=True).start()
    yield
    ui_log(" Shutting down...", "sys")

app = FastAPI(lifespan=lifespan, title="Hedwig OS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(logs.router)
app.include_router(setup.router)

app.mount("/", StaticFiles(directory=".", html=True), name="static")