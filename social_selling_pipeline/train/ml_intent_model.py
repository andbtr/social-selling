import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler


class ClassicMLIntentClassifier:
    """
    Clasificador de intención basado en features tradicionales.
    Completamente independiente de BART.
    """

    def __init__(self):
        self.model = None
        self.vectorizer = TfidfVectorizer(
            max_features=500, ngram_range=(1, 2), min_df=2  # unigrams + bigrams
        )
        self.scaler = StandardScaler()

    def extract_handcrafted_features(self, text: str) -> np.ndarray:
        """
        Extrae features manuales (NO usa BART).
        """
        if not text or not text.strip():
            return np.zeros(15)

        text_lower = text.lower()

        features = [
            # Longitud
            len(text),
            len(text.split()),
            # Puntuación
            1 if "?" in text else 0,
            text.count("?"),
            1 if "!" in text else 0,
            # Keywords de ALTA intención
            1 if any(kw in text_lower for kw in ["precio", "cuánto", "cuanto", "costo"]) else 0,
            1 if any(kw in text_lower for kw in ["reservar", "reserva", "booking"]) else 0,
            (
                1
                if any(kw in text_lower for kw in ["disponible", "disponibilidad", "availability"])
                else 0
            ),
            1 if "urgente" in text_lower else 0,
            # Keywords de MEDIA intención
            1 if any(kw in text_lower for kw in ["piscina", "desayuno", "wifi", "servicio"]) else 0,
            1 if any(kw in text_lower for kw in ["incluye", "tienen", "hay"]) else 0,
            # Keywords de BAJA intención
            1 if any(kw in text_lower for kw in ["hermoso", "lindo", "bonito", "precioso"]) else 0,
            1 if any(kw in text_lower for kw in ["gracias", "thanks"]) else 0,
            1 if any(char in text for char in ["👍", "❤️", "😊"]) else 0,
            # Ratio de palabras interrogativas
            sum(1 for word in ["cómo", "cuánto", "dónde", "cuándo", "qué"] if word in text_lower),
        ]

        return np.array(features)

    def prepare_features(self, texts: list[str]) -> np.ndarray:
        """
        Combina TF-IDF + features manuales.
        """
        # 1. TF-IDF (captura palabras importantes)
        tfidf_features = self.vectorizer.transform(texts).toarray()

        # 2. Features manuales
        manual_features = np.array([self.extract_handcrafted_features(text) for text in texts])

        # 3. Combinar
        combined = np.hstack([tfidf_features, manual_features])

        return combined

    def train(self, texts: list[str], labels: list[str]):
        """
        Entrena el modelo clásico.

        Args:
            texts: Lista de comentarios
            labels: Lista de etiquetas ('ALTA', 'MEDIA', 'BAJA')
        """
        print("Entrenando modelo ML clásico...")

        # Fit vectorizer
        self.vectorizer.fit(texts)

        # Preparar features
        X = self.prepare_features(texts)

        # Escalar features
        X_scaled = self.scaler.fit_transform(X)

        # Entrenar RandomForest
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight="balanced",  # Importante si hay desbalance
        )

        self.model.fit(X_scaled, labels)

        print("✓ Modelo ML clásico entrenado")

    def predict(self, text: str) -> tuple[str, float]:
        """
        Predice intención con modelo clásico.

        Returns:
            tuple: (label, confidence)
        """
        if not self.model:
            raise ValueError("Modelo no entrenado. Llama a train() primero.")

        # Preparar features
        X = self.prepare_features([text])
        X_scaled = self.scaler.transform(X)

        # Predecir
        prediction = self.model.predict(X_scaled)[0]
        proba = self.model.predict_proba(X_scaled)[0]
        confidence = max(proba)

        return prediction, confidence

    def save(self, filepath: str):
        """Guarda modelo entrenado."""
        with open(filepath, "wb") as f:
            pickle.dump(
                {"model": self.model, "vectorizer": self.vectorizer, "scaler": self.scaler}, f
            )
        print(f"✓ Modelo guardado en {filepath}")

    def load(self, filepath: str):
        """Carga modelo entrenado."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.vectorizer = data["vectorizer"]
            self.scaler = data["scaler"]
        print(f"✓ Modelo cargado desde {filepath}")
