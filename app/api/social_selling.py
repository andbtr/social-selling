# app/api/social_selling.py
from fastapi import APIRouter, Depends, Header, HTTPException
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, cast, Date, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.comment import Comment  # tu modelo real
from app.models.lead_score import LeadScore

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
 
def q_window_comments(db: Session, dt_from: datetime, dt_to: datetime):
   """
   Query base filtrando comentarios por ventana de tiempo.
   """
   return db.query(Comment).filter(
       Comment.platform_created_at >= dt_from,
       Comment.platform_created_at < dt_to
   )

def q_window_leads(db: Session, dt_from: datetime, dt_to: datetime):
   """
   Query base filtrando lead scores calculados en la ventana de tiempo.
   Importante: usamos LeadScore.computed_at para la ventana.
   """
   return db.query(LeadScore).filter(
       LeadScore.computed_at >= dt_from,
       LeadScore.computed_at < dt_to
   )

def _count_sentiment(db: Session, dt_from: datetime, dt_to: datetime, kind: str):
   """
   kind in {"positive","neutral","negative"}
   Cuenta cuántos comments en la ventana tienen ese sentimiento (normalizado).
   Lo hacemos con un WHERE ... IN (...) porque así evitamos traer todo y normalizar en Python.
   """
   mapping = {
       "positive": ("positive","pos","+","p","positivo","positiva"),
       "neutral":  ("neutral","neu","=","n"),
       "negative": ("negative","neg","-","g","negativo","negativa"),
   }
   return (
       db.query(func.count())
       .filter(
           Comment.platform_created_at >= dt_from,
           Comment.platform_created_at < dt_to,
           func.lower(Comment.sentiment).in_(mapping[kind])
       )
       .scalar()
   )

def _count_hot_leads(db: Session, dt_from: datetime, dt_to: datetime):
   """
   Cuenta cuántos leads 'hot' hay en la ventana usando LeadScore.priority_level.
   """
   return (
       db.query(func.count())
       .filter(
           LeadScore.computed_at >= dt_from,
           LeadScore.computed_at < dt_to,
           func.lower(LeadScore.priority_level) == "hot"
       )
       .scalar()
   )

# ---------- /stats ----------
@router.get("/stats", dependencies=[Depends(require_api_key)])
def stats(period: str = "30d", platform: str = "all",
          startDate: str | None = None, endDate: str | None = None,
          db: Session = Depends(get_db)):
    dt_from, dt_to = resolve_period(period, startDate, endDate)
    window = dt_to - dt_from
    prev_from, prev_to = dt_from - window, dt_from

    q  = q_window_comments(db, dt_from, dt_to)
    qp = q_window_comments(db, prev_from, prev_to)
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

# ---------- /summary-cards ----------
@router.get("/summary-cards", dependencies=[Depends(require_api_key)])
def summary_cards(
   period: str = "7d",
   startDate: str | None = None,
   endDate: str | None = None,
   db: Session = Depends(get_db)):
   """
   Respuesta ejemplo:
   {
     "positive": { "count":127, "trend":"+12%" },
     "neutral":  { "count":34,  "trend":"+3%"  },
     "negative": { "count":8,   "trend":"-5%"  },
     "leads":    { "count":23,  "trend":"+9%"  }
   }
   """
   dt_from, dt_to = resolve_period(period, startDate, endDate)
   window = dt_to - dt_from
   prev_from, prev_to = dt_from - window, dt_from
   # ventana actual
   c_pos_now = _count_sentiment(db, dt_from, dt_to, "positive")
   c_neu_now = _count_sentiment(db, dt_from, dt_to, "neutral")
   c_neg_now = _count_sentiment(db, dt_from, dt_to, "negative")
   c_lead_now = _count_hot_leads(db, dt_from, dt_to)
   # ventana anterior
   c_pos_prev = _count_sentiment(db, prev_from, prev_to, "positive")
   c_neu_prev = _count_sentiment(db, prev_from, prev_to, "neutral")
   c_neg_prev = _count_sentiment(db, prev_from, prev_to, "negative")
   c_lead_prev = _count_hot_leads(db, prev_from, prev_to)
   return {
       "positive": {
           "count": c_pos_now,
           "trend": pct_change(c_pos_now, c_pos_prev)
       },
       "neutral": {
           "count": c_neu_now,
           "trend": pct_change(c_neu_now, c_neu_prev)
       },
       "negative": {
           "count": c_neg_now,
           "trend": pct_change(c_neg_now, c_neg_prev)
       },
       "leads": {
           "count": c_lead_now,
           "trend": pct_change(c_lead_now, c_lead_prev)
       },
   }

# ---------- /sentiment-distribution ----------
@router.get("/sentiment-distribution", dependencies=[Depends(require_api_key)])
def sentiment_distribution(
   period: str = "7d",
   startDate: str | None = None,
   endDate: str | None = None,
   db: Session = Depends(get_db)):
   """
   Devuelve:
   {
     "positive": { "count": X, "pct": Y },
     "neutral":  { "count": A, "pct": B },
     "negative": { "count": C, "pct": D }
   }
   pct en 0-100 redondeado.
   """
   dt_from, dt_to = resolve_period(period, startDate, endDate)
   c_pos = _count_sentiment(db, dt_from, dt_to, "positive")
   c_neu = _count_sentiment(db, dt_from, dt_to, "neutral")
   c_neg = _count_sentiment(db, dt_from, dt_to, "negative")
   total = c_pos + c_neu + c_neg
   def pct(x: int, tot: int):
       return round((x / tot) * 100) if tot else 0
   return {
       "positive": {"count": c_pos, "pct": pct(c_pos, total)},
       "neutral":  {"count": c_neu, "pct": pct(c_neu, total)},
       "negative": {"count": c_neg, "pct": pct(c_neg, total)},
   }

# ---------- /mentions-by-platform ----------
@router.get("/mentions-by-platform", dependencies=[Depends(require_api_key)])
def mentions_by_platform(
   period: str = "7d",
   startDate: str | None = None,
   endDate: str | None = None,
   db: Session = Depends(get_db)):
   """
   Devuelve lista tipo:
   [
     {"platform":"instagram","mentions":88},
     {"platform":"tripadvisor","mentions":45},
     {"platform":"twitter","mentions":24},
     {"platform":"facebook","mentions":12}
   ]
   """
   dt_from, dt_to = resolve_period(period, startDate, endDate)
   q = (
       db.query(
           func.lower(Comment.platform).label("platform"),
           func.count().label("c")
       )
       .filter(
           Comment.platform_created_at >= dt_from,
           Comment.platform_created_at < dt_to
       )
       .group_by("platform")
   )
   rows = q.all()
   out = []
   for plat, cnt in rows:
       out.append({
           "platform": plat or "unknown",
           "mentions": cnt
       })
   # Ordenar desc para que el front pinte primero la más grande (opcional)
   out.sort(key=lambda x: x["mentions"], reverse=True)
   return out

# ---------- /keywords ---------- (Aun no tenemos tabla de keywords)
# @router.get("/keywords", dependencies=[Depends(require_api_key)])
# def keywords_cloud(
#    period: str = "7d",
#    startDate: str | None = None,
#    endDate: str | None = None,
#    limit: int = 20,
#    db: Session = Depends(get_db)):
#    """
#    Devuelve:
#    [
#      {"keyword":"excelente","count":31},
#      {"keyword":"ubicación","count":27},
#      ...
#    ]
#    """
#    dt_from, dt_to = resolve_period(period, startDate, endDate)
#    subquery con sólo los comments del rango que sí tienen keywords
#    base = (
#        db.query(Comment)
#        .filter(
#            Comment.platform_created_at >= dt_from,
#            Comment.platform_created_at < dt_to,
#            Comment.keywords.isnot(None)  # <- asumiendo columna keywords existe en ORM
#        )
#        .subquery()
#    )
#    unnest en Postgres
#    kw_rows = (
#        db.query(
#            unnest(base.c.keywords).label("kw"),
#            func.count().label("c")
#        )
#        .group_by("kw")
#        .order_by(func.count().desc())
#        .limit(limit)
#        .all()
#    )
#    out = []
#    for kw, c in kw_rows:
#        if kw:
#            out.append({"keyword": kw, "count": c})
#    return out