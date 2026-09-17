from fastapi import APIRouter
from app.config import settings
from app.schemas import SettingsPatch

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    return {
        "buy_weights": settings.buy_weights,
        "sell_weights": settings.sell_weights,
        "default_cooldown_hours": settings.default_cooldown_hours,
        "min_score_change_to_realert": settings.min_score_change_to_realert,
        "timeframes": settings.timeframes,
        "default_target_pct": settings.default_target_pct,
        "default_stop_loss_pct": settings.default_stop_loss_pct,
    }


@router.patch("")
async def patch_settings(payload: SettingsPatch):
    """
    In-memory override for this process. For persistence across restarts,
    write these into a `settings` table — left as in-memory here to keep
    the build lean; swap in a DB-backed row if you want it to survive restarts.
    """
    if payload.buy_weights is not None:
        settings.buy_weights = payload.buy_weights
    if payload.sell_weights is not None:
        settings.sell_weights = payload.sell_weights
    if payload.default_cooldown_hours is not None:
        settings.default_cooldown_hours = payload.default_cooldown_hours
    if payload.min_score_change_to_realert is not None:
        settings.min_score_change_to_realert = payload.min_score_change_to_realert
    return await get_settings()
