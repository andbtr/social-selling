from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.intention_service import analyze_intent, analyze_intent_detailed, is_initialized

router = APIRouter(prefix="/intention", tags=["intent"])


class IntentRequest(BaseModel):
    text: str


class IntentResponse(BaseModel):
    intent: str
    confidence: float


@router.post("/analyze", response_model=IntentResponse)
async def analyze_comment_intent(request: IntentRequest):
    """
    Analiza la intención de reserva de un comentario.
    """
    if not is_initialized():
        raise HTTPException(status_code=503, detail="Servicio de intención no disponible")

    intent, confidence = analyze_intent(request.text)

    return IntentResponse(intent=intent, confidence=confidence)


@router.post("/analyze/detailed")
async def analyze_comment_intent_detailed(request: IntentRequest):
    """
    Análisis detallado con información de ambos modelos.
    """
    if not is_initialized():
        raise HTTPException(status_code=503, detail="Servicio de intención no disponible")

    return analyze_intent_detailed(request.text)
