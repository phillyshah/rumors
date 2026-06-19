from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.database import close_pool, create_pool, load_gazetteers


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await create_pool()
    app.state.gazetteers = await load_gazetteers(app.state.db)
    app.state.gazetteers_dirty = False
    yield
    await close_pool(app.state.db)


app = FastAPI(title="Field Intel API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def reload_gazetteers_if_dirty(request: Request, call_next):
    if getattr(request.app.state, "gazetteers_dirty", False):
        request.app.state.gazetteers = await load_gazetteers(request.app.state.db)
        request.app.state.gazetteers_dirty = False
    return await call_next(request)


from app.routers import auth, notes, search, admin

app.include_router(auth.router, prefix="/auth")
app.include_router(notes.router)
app.include_router(search.router)
app.include_router(admin.router, prefix="/admin")


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)
