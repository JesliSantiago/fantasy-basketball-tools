from fastapi import APIRouter

from app import config

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "data_dir": str(config.DATA_DIR), "season": config.DEFAULT_SEASON}
