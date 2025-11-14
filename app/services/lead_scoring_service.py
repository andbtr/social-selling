from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.comment import Comment
from app.models.lead_score import LeadScore
from app.models.lead_threshold import LeadThreshold

# Sentiment labels
POLARITY = {"POS": 1.0, "NEU": 0.0, "NEG": -0.9}

# Intention labels
INTENT_W = {"ALTA": 1.0, "MEDIA": 0.8, "BAJA": 0.4}


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

        # Fallback por si no hay registro en la tabla
        class T:
            pass

        th = T()
        th.scoring_version = "v2"
        th.alpha = 0.6        # peso intención
        th.beta = 0.4         # peso sentimiento
        th.fkw_min = 0.6
        th.fkw_max = 1.6
        th.hot_min = 80.0
        th.warm_min = 60.0
        th.min_intent_for_hot = 0.5
        return th

    @staticmethod
    def _keyword_factor(text: str, fkw_min: float, fkw_max: float) -> float:
        # Placeholder para lógica futura de keywords
        return clamp(1.0, float(fkw_min), float(fkw_max))

    @staticmethod
    def _map_inputs(c: Comment):
        # ============= SENTIMIENTO =============
        pol = POLARITY.get((c.sentiment or "").upper(), 0.0)
        sconf = clamp(float(c.sentiment_confidence or 0.0), 0.0, 1.0)

        # Base lineal inicial
        sent_base = (pol + 1.0) / 2.0

        if pol > 0:  # POSITIVO
            if sconf > 0.70:
                strength = (sconf - 0.70) / (0.95 - 0.70)
                max_bonus = 0.05
                bonus = strength * max_bonus
            else:
                bonus = 0.0
            sent_pos = clamp(sent_base + bonus, 0.0, 1.0)

        elif pol < 0:  # NEGATIVO
            base_neg = 0.20

            if sconf > 0.70:
                strength = (sconf - 0.70) / (0.95 - 0.70)
                max_penalty = 0.15
                penalty = strength * max_penalty
            else:
                penalty = 0.0

            sent_pos = clamp(base_neg - penalty, 0.15, 0.30)

        else:  # NEUTRO
            sent_pos = 0.5

        # ============= INTENCIÓN =============
        w = INTENT_W.get((c.intention or "").upper(), 0.4)
        iconf = clamp(float(c.intention_confidence or 0.0), 0.0, 1.0)

        intent_base = w

        if iconf > 0.45:
            denom = (0.59 - 0.45) or 1.0
            strength = (iconf - 0.45) / denom
            max_bonus = 0.15
            bonus = strength * max_bonus
        else:
            bonus = 0.0

        intent = clamp(intent_base + bonus, 0.0, 1.0)

        return intent, sent_pos

    @staticmethod
    def compute_and_upsert(db: Session, comment_id: int) -> LeadScore:
        c: Comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id)
            .first()
        )
        if not c:
            raise ValueError("Comment not found")

        th = LeadScoringService._active_thresholds(db)

        intent, sent_pos = LeadScoringService._map_inputs(c)
        fkw = LeadScoringService._keyword_factor(
            c.content or "",
            float(th.fkw_min),
            float(th.fkw_max),
        )

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
            .filter(
                LeadScore.comment_id == c.id,
                LeadScore.scoring_version == th.scoring_version,
            )
            .first()
        )

        now = datetime.now(timezone.utc)

        if existing:
            existing.score = score
            existing.priority_level = priority
            existing.computed_at = now
            db.commit()
            db.refresh(existing)
            return existing

        ls = LeadScore(
            comment_id=c.id,
            score=score,
            priority_level=priority,
            scoring_version=th.scoring_version,
            computed_at=now,
        )
        db.add(ls)
        db.commit()
        db.refresh(ls)
        return ls
