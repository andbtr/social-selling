from app.core.database import SessionLocal
from app.models import Comment, PlatformType
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker("es_ES")

def run():
    db = SessionLocal()

    if db.query(Comment).count() > 0:
        print("Comments ya existen, se omite seed.")
        db.close()
        return

    platforms = list(PlatformType)
    sentiments = ["POS", "NEG", "NEU"]

    positive_comments = [
        "El servicio fue excelente, muy atentos y rápidos.",
        "Me encantó la atención, volvería sin dudarlo.",
        "Todo estuvo perfecto, superaron mis expectativas.",
        "Muy buena experiencia, lo recomiendo totalmente.",
        "El lugar es limpio y el personal muy amable."
    ]

    negative_comments = [
        "La atención fue pésima, no lo recomiendo.",
        "Esperé más de una hora y nadie me atendió.",
        "Muy mala experiencia, no volveré nunca.",
        "El servicio dejó mucho que desear.",
        "Demasiado caro para lo que ofrecen."
    ]

    neutral_comments = [
        "Estuvo bien, nada fuera de lo común.",
        "El servicio fue regular, aunque podría mejorar.",
        "Cumple con lo básico, sin sorpresas.",
        "No está mal, pero hay opciones mejores.",
        "Una experiencia promedio, aceptable."
    ]

    comments = []

    for _ in range(30):
        platform = random.choice(platforms)
        sentiment = random.choice(sentiments)

        if sentiment == "POS":
            content = random.choice(positive_comments)
        elif sentiment == "NEG":
            content = random.choice(negative_comments)
        else:
            content = random.choice(neutral_comments)

        created_time = fake.date_time_between(start_date="-30d", end_date="now")

        comment = Comment(
            platform=platform,
            platform_id=fake.unique.numerify('1########'),
            id_comment_platform=random.randint(1000, 9999),
            author=fake.name(),
            content=content,
            rating=round(random.uniform(1.0, 5.0), 1),
            post_url=f"https://{platform.value}.com/post/{fake.uuid4()}",
            created_at=datetime.utcnow(),
            platform_created_at=created_time,
            sentiment_analized=True,
            sentiment_analized_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            sentiment=sentiment,
            sentiment_confidence=round(random.uniform(0.6, 0.99), 2),
            intention_analized=True,
            intention_analized_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
            intention=random.choice(["ALTA", "MEDIA", "BAJA"]),
            intention_confidence=round(random.uniform(0.6, 0.95), 2),
        )

        comments.append(comment)

    db.add_all(comments)
    db.commit()
    db.close()

    print(f"✅ {len(comments)} comentarios insertados correctamente.")
