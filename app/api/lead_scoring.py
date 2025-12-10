from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.lead_scoring import LeadScoreOut, LeadThresholdOut
from app.services.lead_scoring_service import LeadScoringService
from app.models.lead_threshold import LeadThreshold
from app.models.comment import Comment

router = APIRouter(prefix="/leads", tags=["Lead Scoring"])


@router.post("/score/{comment_id}", response_model=LeadScoreOut)
def score_comment(comment_id: int, db: Session = Depends(get_db)):
    try:
        ls = LeadScoringService.compute_and_upsert(db, comment_id)
        return {
            "comment_id": ls.comment_id,
            "score": float(ls.score),
            "priority_level": ls.priority_level,
            "scoring_version": ls.scoring_version,
            "computed_at": ls.computed_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@router.post("/score/bulk", response_model=dict)
def score_bulk(
    since_id: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    q = db.query(Comment.id).order_by(Comment.id.asc())
    if since_id is not None:
        q = q.filter(Comment.id >= since_id)
    ids = [row[0] for row in q.limit(limit).all()]
    processed, errors = 0, []
    for cid in ids:
        try:
            LeadScoringService.compute_and_upsert(db, cid)
            processed += 1
        except Exception as e:
            errors.append({"comment_id": cid, "error": str(e)})
    return {"processed": processed, "errors": errors}


@router.get("/thresholds/active", response_model=LeadThresholdOut)
def get_active_thresholds(db: Session = Depends(get_db)):
    th = (
        db.query(LeadThreshold)
        .filter(LeadThreshold.active == True)
        .order_by(LeadThreshold.id.desc())
        .first()
    )
    if not th:
        # responde los defaults del servicio
        return {
            "scoring_version": "v1",
            "alpha": 0.7,
            "beta": 0.3,
            "fkw_min": 0.6,
            "fkw_max": 1.6,
            "hot_min": 80.0,
            "warm_min": 60.0,
            "min_intent_for_hot": 0.5,
            "active": True,
        }
    return {
        "scoring_version": th.scoring_version,
        "alpha": float(th.alpha),
        "beta": float(th.beta),
        "fkw_min": float(th.fkw_min),
        "fkw_max": float(th.fkw_max),
        "hot_min": float(th.hot_min),
        "warm_min": float(th.warm_min),
        "min_intent_for_hot": float(th.min_intent_for_hot),
        "active": th.active,
    }
