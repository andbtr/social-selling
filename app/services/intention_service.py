# app/services/intention_service.py
import logging

logger = logging.getLogger(__name__)

# Variable global para el ensemble
_ensemble = None


def initialize_ensemble(ml_model_path: str = None):
    """
    Inicializa el sistema ensemble.
    """
    global _ensemble

    try:
        logger.info("Inicializando clasificador de intención...")

        # ⭐ IMPORT AQUÍ - se ejecuta solo una vez durante startup
        from ml.ensemble.ensemble_intent_classifier import EnsembleIntentClassifier

        _ensemble = EnsembleIntentClassifier(ml_model_path)
        logger.info("✓ Clasificador inicializado correctamente")

        # Test rápido
        test_result = _ensemble.predict_ensemble("Test", method="weighted_average")
        logger.info(f"✓ Test de clasificación exitoso: {test_result[0]}")

    except Exception as e:
        logger.error(f"Error al inicializar ensemble: {e}")
        raise


def analyze_intent(text: str) -> tuple[str, float]:
    """Analiza intención usando ensemble de modelos."""
    if _ensemble is None:
        raise RuntimeError(
            "Ensemble no inicializado. " "Asegúrate de llamar initialize_ensemble() en el startup."
        )

    if not text or not text.strip():
        return "BAJA", 0.0

    try:
        label, confidence, _ = _ensemble.predict_ensemble(text, method="weighted_average")
        return label, confidence
    except Exception as e:
        logger.error(f"Error analyzing intent: {e}")
        return "MEDIA", 0.0


def analyze_intent_detailed(text: str) -> dict:
    """Análisis detallado con información de ambos modelos."""
    if _ensemble is None:
        raise RuntimeError("Ensemble no inicializado.")

    if not text or not text.strip():
        return {"intent": "BAJA", "confidence": 0.0, "bart_prediction": None, "ml_prediction": None}

    try:
        label, confidence, details = _ensemble.predict_ensemble(text, method="weighted_average")

        return {
            "intent": label,
            "confidence": round(confidence, 3),
            "bart_prediction": details["bart"],
            "ml_prediction": details["ml"],
            "combined_probs": details.get("combined_probs"),
        }
    except Exception as e:
        logger.error(f"Error in detailed analysis: {e}")
        return {
            "intent": "MEDIA",
            "confidence": 0.0,
            "bart_prediction": None,
            "ml_prediction": None,
        }


def is_initialized() -> bool:
    """Verifica si el ensemble está inicializado."""
    return _ensemble is not None
