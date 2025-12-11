from transformers import pipeline

# Cargar modelo de clasificación zero-shot
intent_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Categorías de intención
INTENT_CATEGORIES = [
    "this_is_a_customer_asking_how_to_book_or_about_prices_and_availability",
    "this_is_a_customer_asking_about_hotel_services_and_amenities",
    "this_is_a_customer_leaving_a_compliment_not_asking_anything_or_complaining",
]


# Mapeo de categorías a etiquetas simples
def _map_category_to_intent(category: str) -> str:
    """
    Mapea la categoría del modelo a una etiqueta simple.

    Args:
        category (str): Categoría retornada por el modelo

    Returns:
        str: "ALTA", "MEDIA", o "BAJA"
    """
    if "book" in category.lower() or "prices_and_availability" in category.lower():
        return "ALTA"
    elif "services_and_amenities" in category.lower():
        return "MEDIA"
    elif "compliment" in category.lower() or "complaining" in category.lower():
        return "BAJA"
    else:
        return "MEDIA"  # Fallback


def analyze_intent(text: str) -> tuple[str, float]:
    """
    Analyzes the booking intention of the given text using zero-shot classification.

    Args:
        text (str): The text to analyze (customer comment from social media).

    Returns:
        tuple: (intent_label, confidence_score)
               intent_label: "ALTA", "MEDIA", or "BAJA"
               confidence_score: float between 0 and 1
    """
    if not text.strip():
        return "BAJA", 0.0  # Default for empty text

    try:
        result = intent_classifier(text, INTENT_CATEGORIES, multi_label=False)

        # Obtener la categoría con mayor score
        top_category = result["labels"][0]
        confidence = result["scores"][0]

        # Mapear a etiqueta simple
        intent_label = _map_category_to_intent(top_category)

        return intent_label, confidence

    except Exception as e:
        # Log error if needed
        print(f"Error analyzing intent: {e}")
        return "MEDIA", 0.0  # Fallback


# Función opcional: retornar información detallada
def analyze_intent_detailed(text: str) -> dict:
    """
    Analyzes the booking intention with detailed scores for all categories.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: {
            'intent': str ("ALTA", "MEDIA", "BAJA"),
            'confidence': float,
            'all_scores': dict with scores for each category,
            'raw_category': str (original category name)
        }
    """
    if not text.strip():
        return {"intent": "BAJA", "confidence": 0.0, "all_scores": {}, "raw_category": ""}

    try:
        result = intent_classifier(text, INTENT_CATEGORIES, multi_label=False)

        # Obtener la categoría con mayor score
        top_category = result["labels"][0]
        confidence = result["scores"][0]

        # Crear diccionario con todos los scores
        all_scores = {label: score for label, score in zip(result["labels"], result["scores"])}

        # Mapear a etiqueta simple
        intent_label = _map_category_to_intent(top_category)

        return {
            "intent": intent_label,
            "confidence": round(confidence, 3),
            "all_scores": {k: round(v, 3) for k, v in all_scores.items()},
            "raw_category": top_category,
        }

    except Exception as e:
        # Log error if needed
        print(f"Error analyzing intent: {e}")
        return {"intent": "MEDIA", "confidence": 0.0, "all_scores": {}, "raw_category": ""}


# Ejemplo de uso
if __name__ == "__main__":
    # Casos de prueba
    test_comments = [
        "Cuánto cuesta la habitación doble?",
        "Tienen piscina?",
        "Hermoso lugar!",
        "Horrible servicio",
        "Necesito reservar urgente",
    ]

    print("=" * 60)
    print("PRUEBA DE CLASIFICACIÓN DE INTENCIÓN")
    print("=" * 60)

    for comment in test_comments:
        intent, confidence = analyze_intent(comment)
        print(f'\nComentario: "{comment}"')
        print(f"Intención: {intent} (confianza: {confidence:.3f})")

    # Prueba detallada
    print("\n" + "=" * 60)
    print("PRUEBA DETALLADA")
    print("=" * 60)

    detailed = analyze_intent_detailed("Disponibilidad para este fin de semana?")
    print(f'\nComentario: "Disponibilidad para este fin de semana?"')
    print(f"Intención: {detailed['intent']}")
    print(f"Confianza: {detailed['confidence']}")
    print(f"Scores detallados:")
    for cat, score in detailed["all_scores"].items():
        print(f"  - {cat[:50]}...: {score}")
