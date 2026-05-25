from app.base import app
from app.core.config import get_settings

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    cfg = get_settings()
    uvicorn.run("main:app", host=cfg.app_host, port=cfg.app_port, reload=False)
