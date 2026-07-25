import httpx
from datetime import datetime, timezone
from app.core.config import settings

FEED_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
IMPACT_MAP = {"high": 3, "medium": 2, "low": 1, "holiday": 1}
IMPACT_LABELS = {3: "HIGH", 2: "MEDIUM", 1: "LOW"}


async def _fetch_feed():
    async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"}) as client:
        response = await client.get(FEED_URL)
        response.raise_for_status()
        return response.json()


async def get_economic_calendar(from_date=None, to_date=None, country=None, importance=None):
    if not settings.economic_calendar_enabled:
        return []
    try:
        raw = await _fetch_feed()
    except Exception:
        return []

    result = []
    for e in raw:
        impact_level = IMPACT_MAP.get(str(e.get("impact", "")).lower(), 1)
        if importance and impact_level < importance:
            continue
        if country and e.get("country", "").upper() != country.upper():
            continue
        date_part, _, time_part = e.get("date", "").partition("T")
        if from_date and date_part < from_date:
            continue
        if to_date and date_part > to_date:
            continue
        result.append({
            "event": e.get("title", ""),
            "country": e.get("country", ""),
            "date": date_part,
            "time": time_part[:5] if time_part else "",
            "impact": impact_level,
            "impact_label": IMPACT_LABELS.get(impact_level, "LOW"),
            "actual": None,
            "estimate": e.get("forecast") or None,
            "prev": e.get("previous") or None,
            "unit": "",
        })
    result.sort(key=lambda x: (x["date"], x["time"]))
    return result


async def get_high_impact_events(hours_ahead=4):
    if not settings.economic_calendar_enabled:
        return []
    try:
        raw = await _fetch_feed()
    except Exception:
        return []

    now = datetime.now(timezone.utc)
    upcoming = []
    for e in raw:
        if IMPACT_MAP.get(str(e.get("impact", "")).lower(), 1) < 3:
            continue
        try:
            event_time = datetime.fromisoformat(e.get("date", ""))
            diff = (event_time - now).total_seconds() / 3600
            if 0 <= diff <= hours_ahead:
                upcoming.append({
                    "event": e.get("title", ""),
                    "country": e.get("country", ""),
                    "hours_until": round(diff, 1),
                })
        except (ValueError, TypeError):
            continue
    return upcoming


async def should_trade():
    fng = None
    try:
        from app.services.calendar.fear_greed import get_fear_greed_index
        fng = await get_fear_greed_index()
    except Exception:
        pass
    upcoming_events = []
    try:
        upcoming_events = await get_high_impact_events(hours_ahead=2)
    except Exception:
        pass
    can_trade = True
    reasons = []
    if fng:
        if fng["value"] <= 15:
            can_trade = False
            reasons.append(f"Extreme Fear ({fng['value']}) - marche en panique")
        elif fng["value"] >= 85:
            can_trade = False
            reasons.append(f"Extreme Greed ({fng['value']}) - risque de correction")
    if upcoming_events:
        can_trade = False
        event_names = [e["event"] for e in upcoming_events[:3]]
        reasons.append(f"Evenement(s) haute importance dans 2h: {', '.join(event_names)}")
    return {
        "can_trade": can_trade,
        "reasons": reasons,
        "fear_greed": fng,
        "upcoming_high_impact": upcoming_events,
    }
