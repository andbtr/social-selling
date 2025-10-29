# app/api/social_selling.py
from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.comment import Comment  # tu modelo real

router = APIRouter(prefix="/api/social-selling", tags=["social-selling"])

# ---------- Auth ----------
def require_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

# ---------- Helpers ----------
def resolve_period(period: str, start: str | None, end: str | None):
    now = datetime.now(timezone.utc)
    if period == "7d":   return now - timedelta(days=7),  now
    if period == "30d":  return now - timedelta(days=30), now
    if period == "90d":  return now - timedelta(days=90), now
    if period == "custom" and start and end:
        return (datetime.fromisoformat(start.replace("Z","+00:00")),
                datetime.fromisoformat(end.replace("Z","+00:00")))
    raise HTTPException(422, "Invalid period/startDate/endDate")

# Mapeo robusto de sentimiento -> etiquetas ES del dashboard
def _sentiment_norm(s: str | None) -> str | None:
    if not s: return None
    s = s.lower()
    if s in {"positive","pos","+","p"}: return "positive"
    if s in {"neutral","neu","=","n"}:  return "neutral"
    if s in {"negative","neg","-","g"}: return "negative"
    return None  # descarta valores desconocidos

# Intención “alta”
def _is_high_intention(val: str | None) -> bool:
    if not val: return False
    v = val.lower()
    return v in {"high","alta","alto","hi"}

def pct_change(curr: float | int, prev: float | int) -> str:
    if prev in (0, None): return "0%" if not curr else "100%"
    return f"{((curr - prev) / prev) * 100:.0f}%"

def q_window(db: Session, dt_from: datetime, dt_to: datetime):
    return db.query(Comment).filter(
        Comment.platform_created_at >= dt_from,
        Comment.platform_created_at < dt_to
    )

# ---------- /stats ----------
@router.get("/stats", dependencies=[Depends(require_api_key)])
def stats(period: str = "30d", platform: str = "all",
          startDate: str | None = None, endDate: str | None = None,
          db: Session = Depends(get_db)):
    dt_from, dt_to = resolve_period(period, startDate, endDate)
    window = dt_to - dt_from
    prev_from, prev_to = dt_from - window, dt_from

    q  = q_window(db, dt_from, dt_to)
    qp = q_window(db, prev_from, prev_to)
    if platform != "all":
        q  = q.filter(Comment.platform == platform)
        qp = qp.filter(Comment.platform == platform)

    total = q.count()

    # Conteos por sentimiento (normalizados)
    pos = q.filter(func.lower(Comment.sentiment).in_(("positive","pos","+","p"))).count()
    neu = q.filter(func.lower(Comment.sentiment).in_(("neutral","neu","=","n"))).count()
    neg = q.filter(func.lower(Comment.sentiment).in_(("negative","neg","-","g"))).count()

    high_intent = q.filter(func.lower(Comment.intention).in_(("high","alta","alto","hi"))).count()

    # Hot leads (por ahora = intención alta; cuando tengas lead_score, cámbialo)
    hot = high_intent

    pos_pct = round((pos / total) * 100) if total else 0

    # Ventana anterior
    prev_total = qp.count()
    prev_pos = qp.filter(func.lower(Comment.sentiment).in_(("positive","pos","+","p"))).count()
    prev_high = qp.filter(func.lower(Comment.intention).in_(("high","alta","alto","hi"))).count()
    prev_hot  = prev_high  # igual que arriba

    prev_pos_pct = round((prev_pos / prev_total) * 100) if prev_total else 0

    return {
        "totalMentions": total,
        "positiveSentiment": pos_pct,
        "highIntention": high_intent,
        "hotLeads": hot,
        "trends": {
            "mentions":  pct_change(total, prev_total),
            "sentiment": pct_change(pos_pct, prev_pos_pct),
            "intention": pct_change(high_intent, prev_high),
            "leads":     pct_change(hot, prev_hot),
        }
    }

# ---------- /sentiment-trend ----------
@router.get("/sentiment-trend", dependencies=[Depends(require_api_key)])
def sentiment_trend(period: str = "30d", platform: str = "all",
                    startDate: str | None = None, endDate: str | None = None,
                    db: Session = Depends(get_db)):
    dt_from, dt_to = resolve_period(period, startDate, endDate)
    q = db.query(
        cast(Comment.platform_created_at, Date).label("d"),
        func.lower(Comment.sentiment).label("s"),
        func.count().label("c")
    ).filter(
        Comment.platform_created_at >= dt_from,
        Comment.platform_created_at < dt_to
    )
    if platform != "all":
        q = q.filter(Comment.platform == platform)

    rows = q.group_by("d", "s").order_by("d").all()

    out = {}
    for d, s_raw, c in rows:
        s = _sentiment_norm(s_raw)
        if not s:  # ignora valores desconocidos
            continue
        key = d.isoformat()
        out.setdefault(key, {"date": key, "positivo": 0, "neutral": 0, "negativo": 0})
        if s == "positive": out[key]["positivo"] = c
        elif s == "neutral": out[key]["neutral"] = c
        elif s == "negative": out[key]["negativo"] = c

    return sorted(out.values(), key=lambda x: x["date"])

# ---------- /mentions ----------
@router.get("/mentions", dependencies=[Depends(require_api_key)])
def mentions(period: str = "30d", platform: str = "all",
             startDate: str | None = None, endDate: str | None = None,
             limit: int = 20, offset: int = 0,
             db: Session = Depends(get_db)):
    dt_from, dt_to = resolve_period(period, startDate, endDate)
    q = db.query(Comment).filter(
        Comment.platform_created_at >= dt_from,
        Comment.platform_created_at < dt_to
    )
    if platform != "all":
        q = q.filter(Comment.platform == platform)

    rows = q.order_by(Comment.platform_created_at.desc()).offset(offset).limit(limit).all()

    items = [{
        "id": r.id,
        "platform": getattr(r, "platform", None),
        "author": getattr(r, "author", None),
        "content": getattr(r, "content", None),
        "created_at": r.platform_created_at.isoformat() if getattr(r, "platform_created_at", None) else None,
        "sentiment": _sentiment_norm(getattr(r, "sentiment", None)),
        "intention": getattr(r, "intention", None),
        "rating": getattr(r, "rating", None),
        "post_url": getattr(r, "post_url", None),
    } for r in rows]

    return {"items": items, "next_offset": offset + limit}
