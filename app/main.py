from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db
from app.core.demo_store import demo_store
from app.modules.routing.dispatcher import department_dispatcher
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed only if empty
    init_db()
    demo_store.seed_if_empty()
    department_dispatcher.load_from_db()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multimodal Civic Issue Detection & Priority Advisory Engine (NLP + YOLO + GIS)",
    lifespan=lifespan
)

# Restricted CORS for authorized dashboard and client origins
cors_origins = settings.allowed_origins_list
has_wildcard = "*" in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not has_wildcard,  # Unsafe wildcard-plus-credentials is strictly forbidden
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)


import os
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if os.path.exists("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/")
def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {
        "title": settings.app_name,
        "dashboard": "/dashboard",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "issues": "/api/v1/issues",
            "gis_geojson": "/api/v1/gis/geojson",
            "reset_demo": "/api/v1/demo/reset"
        }
    }

@app.get("/dashboard")
@app.get("/dashboard/{full_path:path}")
def serve_dashboard():
    if os.path.exists("frontend/dist/index.html"):
        return FileResponse("frontend/dist/index.html")
    return {"message": "Frontend build not found. Please build frontend first."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
