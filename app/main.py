from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.routes import router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Multimodal Civic Issue Detection & Priority Advisory Engine (NLP + YOLO + GIS)"
)

# Enable CORS for flexible dashboard/frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
