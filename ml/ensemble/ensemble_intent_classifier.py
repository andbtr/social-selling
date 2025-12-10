# ensemble_intent_classifier.py
from transformers import pipeline
from social_selling_pipeline.train.ml_intent_model import ClassicMLIntentClassifier


class EnsembleIntentClassifier:
    """
    Combina predicciones de BART + ML Clásico.
    """

    def __init__(self, ml_model_path: str = None):
        # Modelo 1: BART
        print("Cargando BART...")
        self.bart_classifier = pipeline(
            "zero-shot-classification", model="facebook/bart-large-mnli"
        )

        self.categories = [
            "this_is_a_customer_asking_how_to_book_or_about_prices_and_availability",
            "this_is_a_customer_asking_about_hotel_services_and_amenities",
            "this_is_a_customer_leaving_a_compliment_not_asking_anything_or_complaining",
        ]

        # Modelo 2: ML Clásico
        print("Cargando modelo ML clásico...")
        self.ml_classifier = ClassicMLIntentClassifier()
        if ml_model_path:
            self.ml_classifier.load(ml_model_path)

        # Pesos para combinación (puedes ajustar)
        self.bart_weight = 0.6
        self.ml_weight = 0.4

    def _bart_predict(self, text: str) -> tuple[str, dict]:
        """Predicción con BART."""
        result = self.bart_classifier(text, self.categories, multi_label=False)

        top_category = result["labels"][0]

        # Mapear a label simple
        if "book" in top_category or "prices_and_availability" in top_category:
            label = "ALTA"
        elif "services_and_amenities" in top_category:
            label = "MEDIA"
        else:
            label = "BAJA"

        # Crear dict de probabilidades
        probs = {}
        for cat, score in zip(result["labels"], result["scores"]):
            if "book" in cat or "prices_and_availability" in cat:
                probs["ALTA"] = score
            elif "services_and_amenities" in cat:
                probs["MEDIA"] = score
            else:
                probs["BAJA"] = score

        return label, probs

    def _ml_predict(self, text: str) -> tuple[str, dict]:
        """Predicción con ML clásico."""
        label, confidence = self.ml_classifier.predict(text)

        # Obtener probabilidades de todas las clases
        X = self.ml_classifier.prepare_features([text])
        X_scaled = self.ml_classifier.scaler.transform(X)
        proba = self.ml_classifier.model.predict_proba(X_scaled)[0]
        classes = self.ml_classifier.model.classes_

        probs = {cls: prob for cls, prob in zip(classes, proba)}

        return label, probs

    def predict_ensemble(
        self, text: str, method: str = "weighted_average"
    ) -> tuple[str, float, dict]:
        """
        Predicción combinada de ambos modelos.

        Args:
            text: Texto a clasificar
            method: 'weighted_average', 'voting', 'max_confidence'

        Returns:
            tuple: (label, confidence, details)
        """
        if not text or not text.strip():
            return "BAJA", 0.0, {}

        # Predicción de BART
        bart_label, bart_probs = self._bart_predict(text)

        # Predicción de ML
        ml_label, ml_probs = self._ml_predict(text)

        # COMBINAR según método
        if method == "weighted_average":
            # Promedio ponderado de probabilidades
            combined_probs = {}
            for label in ["ALTA", "MEDIA", "BAJA"]:
                bart_prob = bart_probs.get(label, 0.0)
                ml_prob = ml_probs.get(label, 0.0)
                combined_probs[label] = self.bart_weight * bart_prob + self.ml_weight * ml_prob

            final_label = max(combined_probs, key=combined_probs.get)
            confidence = combined_probs[final_label]

        elif method == "voting":
            # Votación simple
            if bart_label == ml_label:
                final_label = bart_label
                confidence = (bart_probs[bart_label] + ml_probs[ml_label]) / 2
            else:
                # Desempate por confianza
                bart_conf = bart_probs[bart_label]
                ml_conf = ml_probs[ml_label]

                if bart_conf > ml_conf:
                    final_label = bart_label
                    confidence = bart_conf
                else:
                    final_label = ml_label
                    confidence = ml_conf

        else:  # max_confidence
            # Elegir el que tenga mayor confianza
            if bart_probs[bart_label] > ml_probs[ml_label]:
                final_label = bart_label
                confidence = bart_probs[bart_label]
            else:
                final_label = ml_label
                confidence = ml_probs[ml_label]

        # Detalles
        details = {
            "bart": {"label": bart_label, "probs": bart_probs},
            "ml": {"label": ml_label, "probs": ml_probs},
            "combined_probs": combined_probs if method == "weighted_average" else None,
        }

        return final_label, confidence, details
