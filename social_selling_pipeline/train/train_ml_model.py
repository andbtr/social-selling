# train_ml_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from ml_intent_model import ClassicMLIntentClassifier

# 1. Cargar datos
df = pd.read_csv("social_selling_pipeline/data/raw/training_data.csv")

print(f"Total ejemplos: {len(df)}")
print(f"\nDistribución:")
print(df["label"].value_counts())

# 2. Split 80/20
X_train, X_test, y_train, y_test = train_test_split(
    df["text"].tolist(), df["label"].tolist(), test_size=0.2, stratify=df["label"], random_state=42
)

print(f"\nTrain: {len(X_train)} ejemplos")
print(f"Test: {len(X_test)} ejemplos")

# 3. Entrenar
classifier = ClassicMLIntentClassifier()
classifier.train(X_train, y_train)

# 4. Evaluar
predictions = []
confidences = []

for text in X_test:
    pred, conf = classifier.predict(text)
    predictions.append(pred)
    confidences.append(conf)

# 5. Métricas
print("\n" + "=" * 60)
print("REPORTE DE CLASIFICACIÓN")
print("=" * 60)
print(classification_report(y_test, predictions))

print("\n" + "=" * 60)
print("MATRIZ DE CONFUSIÓN")
print("=" * 60)
print(confusion_matrix(y_test, predictions))
print("\nOrden: ALTA, BAJA, MEDIA")

# 6. Confianza promedio
import numpy as np

print(f"\nConfianza promedio: {np.mean(confidences):.3f}")
print(f"Confianza mínima: {np.min(confidences):.3f}")
print(f"Confianza máxima: {np.max(confidences):.3f}")

# 7. Guardar
classifier.save("ml/models/ml_intent_model.pkl")
print("\n✓ Modelo guardado en 'ml/models/ml_intent_model.pkl'")
