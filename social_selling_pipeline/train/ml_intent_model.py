import re
import unicodedata
import numpy as np
from difflib import SequenceMatcher
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import pickle


class ClassicMLIntentClassifier:
    """
    Clasificador robusto con:
    - Normalización de texto
    - Fuzzy keyword matching
    - Character n-grams en TF-IDF
    - Features adicionales
    """

    def __init__(self):
        self.model = None

        # TF-IDF combinado: word + character n-grams
        self.word_vectorizer = TfidfVectorizer(max_features=300, ngram_range=(1, 2), min_df=2)

        self.char_vectorizer = TfidfVectorizer(
            max_features=200, analyzer="char_wb", ngram_range=(3, 5), min_df=2
        )

        self.scaler = StandardScaler()

    def normalize_text(self, text: str) -> str:
        """Normalización robusta."""
        if not text:
            return ""
        text = text.lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join([c for c in text if not unicodedata.combining(c)])
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def fuzzy_keyword_match(self, text: str, keyword: str, threshold: float = 0.83) -> bool:
        """Match tolerante a typos."""
        text_norm = self.normalize_text(text)
        words = text_norm.split()

        for word in words:
            if len(word) < 3:
                continue
            similarity = SequenceMatcher(None, word, keyword).ratio()
            if similarity >= threshold:
                return True
        return False

    def extract_handcrafted_features(self, text: str) -> np.ndarray:
        """Features robustas con fuzzy matching."""
        if not text or not text.strip():
            return np.zeros(22)

        text_norm = self.normalize_text(text)

        features = [
            # Longitud
            len(text),
            len(text.split()),
            # Puntuación
            1 if "?" in text else 0,
            text.count("?"),
            1 if "!" in text else 0,
            # ALTA intención - con fuzzy matching
            1 if any(kw in text_norm for kw in ["precio", "cuanto", "costo"]) else 0,
            1 if self.fuzzy_keyword_match(text, "reservar", 0.83) else 0,
            1 if self.fuzzy_keyword_match(text, "reserva", 0.83) else 0,
            1 if self.fuzzy_keyword_match(text, "disponible", 0.85) else 0,
            1 if any(kw in text_norm for kw in ["urgente", "ya", "ahora"]) else 0,
            1 if any(kw in text_norm for kw in ["quiero", "necesito", "deseo", "quisiera"]) else 0,
            # MEDIA intención
            1 if any(kw in text_norm for kw in ["piscina", "desayuno", "wifi"]) else 0,
            1 if any(kw in text_norm for kw in ["incluye", "tienen", "hay"]) else 0,
            # BAJA intención
            1 if any(kw in text_norm for kw in ["hermoso", "lindo", "bonito"]) else 0,
            1 if any(kw in text_norm for kw in ["gracias", "thanks"]) else 0,
            1 if any(c in text for c in ["👍", "❤️", "😊"]) else 0,
            # Features adicionales
            sum(1 for w in ["como", "cuanto", "donde"] if w in text_norm),
            np.mean([len(w) for w in text.split()]) if text.split() else 0,
            1 if re.search(r"\d", text) else 0,
            # Combinaciones poderosas
            (
                1
                if (
                    any(v in text_norm for v in ["quiero", "necesito"])
                    and self.fuzzy_keyword_match(text, "reservar", 0.8)
                )
                else 0
            ),
            1 if (("precio" in text_norm or "cuanto" in text_norm) and "?" in text) else 0,
            (
                1 if len(text.split()) <= 3 and "?" not in text else 0
            ),  # Comentarios muy cortos sin pregunta
        ]

        return np.array(features)

    def prepare_features(self, texts: list[str]) -> np.ndarray:
        """Combina TF-IDF (word + char) + features manuales."""
        # TF-IDF por palabras
        word_features = self.word_vectorizer.transform(texts).toarray()

        # TF-IDF por caracteres (captura typos)
        char_features = self.char_vectorizer.transform(texts).toarray()

        # Features manuales
        manual_features = np.array([self.extract_handcrafted_features(text) for text in texts])

        # Combinar todo
        combined = np.hstack([word_features, char_features, manual_features])

        return combined

    def train(self, texts: list[str], labels: list[str]):
        """Entrena con features mejoradas."""
        print("Entrenando modelo ML mejorado...")

        # Fit vectorizers
        self.word_vectorizer.fit(texts)
        self.char_vectorizer.fit(texts)

        # Preparar features
        X = self.prepare_features(texts)
        X_scaled = self.scaler.fit_transform(X)

        # Entrenar RandomForest
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            class_weight="balanced",
        )

        self.model.fit(X_scaled, labels)
        print("✓ Modelo ML mejorado entrenado")

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
                {
                    "model": self.model,
                    "word_vectorizer": self.word_vectorizer,  # ⭐ CORREGIDO
                    "char_vectorizer": self.char_vectorizer,  # ⭐ NUEVO
                    "scaler": self.scaler,
                },
                f,
            )
        print(f"✓ Modelo guardado en {filepath}")

    def load(self, filepath: str):
        """Carga modelo entrenado."""
        with open(filepath, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.word_vectorizer = data["word_vectorizer"]  # ⭐ CORREGIDO
            self.char_vectorizer = data["char_vectorizer"]  # ⭐ NUEVO
            self.scaler = data["scaler"]
        print(f"✓ Modelo cargado desde {filepath}")
