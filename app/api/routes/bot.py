# app/api/routes/bot.py
from fastapi import APIRouter, Depends
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.bot_runner import bot_cycle
from app.services.scalp_runner import scalp_cycle
from app.core.scheduler import scheduler

router = APIRouter()


def _job_status(job_id: str, interval: str) -> dict:
    job = scheduler.get_job(job_id)
    if not job:
        return {"running": False}
    return {
        "running": True,
        "interval": interval,
        "next_run": str(job.next_run_time),
    }


@router.post("/run-now")
async def run_bot_now(current_user: User = Depends(get_current_user)):
    await bot_cycle()
    return {"detail": "Cycle execute manuellement"}


@router.post("/run-now/scalp")
async def run_scalp_now(current_user: User = Depends(get_current_user)):
    await scalp_cycle()
    return {"detail": "Cycle scalp execute manuellement"}


@router.get("/status")
def bot_status(current_user: User = Depends(get_current_user)):
    return _job_status("bot_cycle", "5 minutes")


@router.get("/status/scalp")
def scalp_status(current_user: User = Depends(get_current_user)):
    return _job_status("scalp_cycle", "1 minute")
