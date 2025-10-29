from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.comment import Comment
from app.models.lead_score import LeadScore
from app.models.lead_threshold import LeadThreshold

POLARITY = {"POS": 1.0, "NEU": 0.0, "NEG": -1.0}
INTENT_W = {"ALTA": 1.0, "MEDIA": 0.7, "BAJA": 0.4}

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

class LeadScoringService:
    @staticmethod
    def _active_thresholds(db: Session) -> LeadThreshold:
        th = (
            db.query(LeadThreshold)
              .filter(LeadThreshold.active == True)
              .order_by(LeadThreshold.id.desc())
              .first()
        )
        if th:
            return th
        # fallback por si no hay registro
        class T: pass
        th = T()
        th.scoring_version="v1"; th.alpha=0.7; th.beta=0.3
        th.fkw_min=0.6; th.fkw_max=1.6
        th.hot_min=80.0; th.warm_min=60.0; th.min_intent_for_hot=0.5
        return th

    @staticmethod
    def _keyword_factor(text: str, fkw_min: float, fkw_max: float) -> float:
        # V1: placeholder (cuando tengas extractor, calcula bonus/penalty y capa entre [fkw_min, fkw_max])
        return clamp(1.0, float(fkw_min), float(fkw_max))

    @staticmethod
    def _map_inputs(c: Comment):
        # Sentiment: label (+ confianza) => [-1,1] => [0,1]
        pol = POLARITY.get((c.sentiment or "").upper(), 0.0)
        sconf = clamp(float(c.sentiment_confidence or 0.0), 0.0, 1.0)
        sentiment_raw = pol * sconf
        sent_pos = (sentiment_raw + 1.0) / 2.0

        # Intention: pondera por ALTA/MEDIA/BAJA
        w = INTENT_W.get((c.intention or "").upper(), 0.4)
        iconf = clamp(float(c.intention_confidence or 0.0), 0.0, 1.0)
        intent = clamp(iconf * w, 0.0, 1.0)
        return intent, sent_pos

    @staticmethod
    def compute_and_upsert(db: Session, comment_id: int) -> LeadScore:
        c: Comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not c:
            raise ValueError("Comment not found")

        th = LeadScoringService._active_thresholds(db)
        intent, sent_pos = LeadScoringService._map_inputs(c)
        fkw = LeadScoringService._keyword_factor(c.content or "", th.fkw_min, th.fkw_max)

        score = 100.0 * (intent ** float(th.alpha)) * (sent_pos ** float(th.beta)) * float(fkw)
        score = round(score, 2)

        if score >= float(th.hot_min) and intent >= float(th.min_intent_for_hot):
            priority = "HOT"
        elif score >= float(th.warm_min):
            priority = "WARM"
        else:
            priority = "COLD"

        existing = (
            db.query(LeadScore)
              .filter(LeadScore.comment_id == c.id, LeadScore.scoring_version == th.scoring_version)
              .first()
        )
        if existing:
            existing.score = score
            existing.priority_level = priority
            existing.computed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        ls = LeadScore(
            comment_id=c.id,
            score=score,
            priority_level=priority,
            scoring_version=th.scoring_version,
            computed_at=datetime.now(timezone.utc),
        )
        db.add(ls)
        db.commit()
        db.refresh(ls)
        return ls
