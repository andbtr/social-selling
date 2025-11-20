from sqlalchemy.orm import Session
from collections import Counter

from app.models.comment_keyword import CommentKeyword
from app.services.llm_client import LLMClient


class KeywordService:

    @staticmethod
    def analyze_comment_keywords(db: Session, comment, max_keywords: int = 3):
        text = comment.content or ""
        if not text.strip():
            return []

        # 1. Extraer keywords con Gemini
        keywords = LLMClient.extract_keywords(text, max_keywords=max_keywords)

        created = []

        if not keywords:
            return created

        # 2. Calcular frecuencia dentro del comentario
        words = [w.lower().strip(".,;:!?¡¿") for w in text.split()]
        counter = Counter(words)

        for kw in keywords:
            freq = counter.get(kw, 1)

            item = CommentKeyword(
                comment_id=comment.id,
                keyword=kw,
                frequency=freq,
            )

            db.add(item)
            created.append(item)

        db.commit()

        for item in created:
            db.refresh(item)

        return created
