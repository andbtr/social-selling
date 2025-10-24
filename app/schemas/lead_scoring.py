from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LeadScoreOut(BaseModel):
    comment_id: int
    score: float
    priority_level: str
    scoring_version: str
    computed_at: datetime

    class Config:
        from_attributes = True

class LeadThresholdOut(BaseModel):
    scoring_version: str
    alpha: float
    beta: float
    fkw_min: float
    fkw_max: float
    hot_min: float
    warm_min: float
    min_intent_for_hot: float
    active: bool
