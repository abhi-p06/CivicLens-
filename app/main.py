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

@app.get("/")
def root():
    return {
        "title": settings.app_name,
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "issues": "/api/v1/issues",
            "gis_geojson": "/api/v1/gis/geojson",
            "reset_demo": "/api/v1/demo/reset"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
