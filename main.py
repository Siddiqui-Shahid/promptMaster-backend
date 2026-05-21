from app.base import app
from app.buisness import router as business_router
from app.core.config import get_settings

# Backward-compatible business route alias
app.include_router(business_router)

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()

    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=False)
