import sys
import os

# --- Ajuste de ruta al root del proyecto ---
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Imports del proyecto ---
from app.core.database import SessionLocal
from app.models.comment import Comment
from app.models.lead_score import LeadScore
from app.services.lead_scoring_service import LeadScoringService


def recompute_all_lead_scores():
    db = SessionLocal()
    try:
        # Usamos los thresholds activos actuales (los mismos que usarías en producción)
        th = LeadScoringService._active_thresholds(db)

        comments = db.query(Comment).all()
        total = len(comments)

        if total == 0:
            print("⚠️ No se encontraron comentarios en la base de datos.")
            return

        print(f"🔁 Recalculando lead scoring para {total} comentarios usando lógica v2 (sin tocar compute_and_upsert)...\n")

        processed = 0
        created = 0
        updated = 0
        errors = 0

        for c in comments:
            comment_id = c.id

            try:
                # 1) Calculamos intent y sentimiento con la lógica actual del servicio
                intent, sent_pos = LeadScoringService._map_inputs(c)

                # 2) Factor de keywords (por ahora fijo en 1.0 dentro del rango)
                fkw = LeadScoringService._keyword_factor(
                    c.content or "",
                    float(th.fkw_min),
                    float(th.fkw_max),
                )

                # 3) Score según fórmula vigente
                score = 100.0 * (intent ** float(th.alpha)) * (sent_pos ** float(th.beta)) * float(fkw)
                score = round(score, 2)

                # 4) Priority según thresholds
                if score >= float(th.hot_min) and intent >= float(th.min_intent_for_hot):
                    priority = "HOT"
                elif score >= float(th.warm_min):
                    priority = "WARM"
                else:
                    priority = "COLD"

                # 5) Upsert manual respetando UNIQUE(comment_id)
                existing = (
                    db.query(LeadScore)
                    .filter(LeadScore.comment_id == comment_id)
                    .first()
                )

                now = datetime.now(timezone.utc)

                if existing:
                    existing.score = score
                    existing.priority_level = priority
                    # Opcional: dejamos claro que fue calculado con la nueva lógica
                    existing.scoring_version = getattr(th, "scoring_version", "v2")
                    existing.computed_at = now
                    updated += 1
                else:
                    ls = LeadScore(
                        comment_id=comment_id,
                        score=score,
                        priority_level=priority,
                        scoring_version=getattr(th, "scoring_version", "v2"),
                        computed_at=now,
                    )
                    db.add(ls)
                    created += 1

                processed += 1

            except Exception as e:
                db.rollback()
                errors += 1
                print(f"❌ Error procesando comment_id={comment_id}: {e}")

        db.commit()

        print("\n✅ Proceso completado.")
        print(f"   ✔ Comentarios procesados: {processed}/{total}")
        print(f"   🆕 Nuevos lead_scores creados: {created}")
        print(f"   📝 Lead_scores actualizados: {updated}")
        if errors:
            print(f"   ❌ Comentarios con error: {errors}")

    finally:
        db.close()


if __name__ == "__main__":
    from datetime import datetime, timezone  # aseguramos import aquí
    recompute_all_lead_scores()
    print("\n✨ Migración de lead scoring finalizada.")
