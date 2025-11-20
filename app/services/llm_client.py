# app/services/llm_client.py

import json
from google import genai
from app.core.config import settings


class LLMClient:
    _client: genai.Client | None = None

    @classmethod
    def get_client(cls) -> genai.Client:
        if cls._client is None:
            if not settings.gemini_api_key:
                raise RuntimeError("GEMINI_API_KEY / settings.gemini_api_key no está configurado")
            cls._client = genai.Client(api_key=settings.gemini_api_key)
        return cls._client

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 3):
        """
        Llama al modelo Gemini para extraer keywords de un comentario.
        Debe retornar un JSON: ["keyword1", "keyword2", ...]
        """

        prompt = f"""
        Extrae entre 1 y {max_keywords} palabras clave del siguiente comentario de redes sociales.
        Reglas:
        - Cada palabra clave debe ser una sola palabra.
        - De acuerdo a la longitud del comentario, puedes extraer menos de {max_keywords} si no hay suficientes.
        - Sin hashtags, sin emojis, sin signos raros.
        - Todo en minúsculas.
        - Sin repetir.
        - DEVUELVE SOLO UN ARRAY JSON, SIN TEXTO ADICIONAL, SIN ```.
        
        Comentario:
        {text}

        Ejemplo de respuesta válida:
        ["reserva", "check-in", "servicio"]
        """

        client = LLMClient.get_client()

        try:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )

            raw = resp.text.strip()
            print("[Gemini raw response]:", raw)

            # --- Normalizar: quitar ``` y texto extra ---
            # 1) Si viene envuelto en ```...```, limpiamos
            if raw.startswith("```"):
                # separa por bloques ``` y toma el contenido del medio
                parts = raw.split("```")
                # parts: ["", "json\n[...]", "" ] o similar
                if len(parts) >= 2:
                    raw = parts[1].strip()  # puede empezar con 'json\n'
                    if raw.lower().startswith("json"):
                        raw = raw[4:].strip()  # quitar 'json' y dejar el array

            # 2) Como último recurso: buscar el [ ... ]
            if not (raw.strip().startswith("[") and raw.strip().endswith("]")):
                start = raw.find("[")
                end = raw.rfind("]")
                if start != -1 and end != -1 and end > start:
                    raw = raw[start:end+1]

            # Ahora raw debería ser solo el JSON
            data = json.loads(raw)

            if not isinstance(data, list):
                return []

            cleaned: list[str] = []
            for kw in data:
                if isinstance(kw, str):
                    kw_clean = kw.strip().lower()
                    if kw_clean:
                        cleaned.append(kw_clean)

            # máximo 3 y sin duplicados
            return list(dict.fromkeys(cleaned))[:max_keywords]

        except Exception as e:
            print(f"[LLMClient] Error procesando Gemini: {e}")
            return []
