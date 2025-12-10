# preload_models.py
import nltk
from transformers import pipeline

print("⬇️ Descargando datos de NLTK...")
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

print("⬇️ Descargando modelo BART (Intención)...")
# Esto descarga el modelo y lo guarda en caché local
pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

print("⬇️ Descargando modelo Robertuito (Sentimiento)...")
# El nuevo culpable que vimos en los logs
pipeline("sentiment-analysis", model="pysentimiento/robertuito-sentiment-analysis")

print("✅ Todo descargado correctamente.")
