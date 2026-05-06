import httpx
from typing import Dict, List
from datetime import datetime, timedelta
from app.core.config import settings

IMPACT_MAP = {"low": 1, "medium": 2, "high": 3}

async def get_economic_calendar(from_date=None, to_date=None, country=None, importance=None):
    api_key = getattr(settings, "finnhub_api_key", None)
    if not api_key:
        return []
    if not from_date:
        from_date = datetime.utcnow().strftime("%Y-%m-%d")
    if not to_date:
        to_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
    url = "https://finnhub.io/api/v1/calendar/economic"
    params = {"from": from_date, "to": to_date, "token": api_key}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        data = response.json()
    events = data.get("economicCalendar", [])
    if country:
        events = [e for e in events if e.get("country", "").upper() == country.upper()]
    if importance:
        events = [e for e in events if IMPACT_MAP.get(str(e.get("impact", "")).lower(), 0) >= importance]
    result = []
    for e in events:
        impact_level = IMPACT_MAP.get(str(e.get("impact", "low")).lower(), 0)
        if impact_level >= 3:
            impact_label = "HIGH"
        elif impact_level >= 2:
            impact_label = "MEDIUM"
        else:
            impact_label = "LOW"
        result.append({
            "event": e.get("event", ""),
            "country": e.get("country", ""),
            "date": e.get("time", ""),
            "impact": impact_level,
            "impact_label": impact_label,
            "actual": e.get("actual"),
            "estimate": e.get("estimate"),
            "prev": e.get("prev"),
            "unit": e.get("unit", ""),
        })
    result.sort(key=lambda x: x["date"])
    return result

async def get_high_impact_events(hours_ahead=4):
    api_key = getattr(settings, "finnhub_api_key", None)
    if not api_key:
        return []
    now = datetime.utcnow()
    from_date = now.strftime("%Y-%m-%d")
    to_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    events = await get_economic_calendar(from_date, to_date, importance=3)
    upcoming = []
    for e in events:
        try:
            event_time = datetime.fromisoformat(e["date"].replace("Z", ""))
            diff = (event_time - now).total_seconds() / 3600
            if 0 <= diff <= hours_ahead:
                e["hours_until"] = round(diff, 1)
                upcoming.append(e)
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