from transformers import pipeline

analyzer = pipeline("sentiment-analysis", model="pysentimiento/robertuito-sentiment-analysis")


def analize_sentiment(text: str) -> tuple[str, float]:
    """
    Analyzes the sentiment of the given text using the Robertuito model.

    Args:
        text (str): The text to analyze.

    Returns:
        tuple: (sentiment_label, confidence_score)
               sentiment_label: "POS", "NEG", or "NEU"
               confidence_score: float between 0 and 1
    """
    if not text.strip():
        return "NEU", 0.0  # Default for empty text

    try:
        result = analyzer(text)[0]
        label = result["label"]
        score = result["score"]
        return label, score
    except Exception as e:
        # Log error if needed
        return "NEU", 0.0  # Fallback