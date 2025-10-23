#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, re, argparse, unicodedata
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# ---------- RUTAS / .env / ENGINE ----------
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ENV_PATH     = PROJECT_ROOT / ".env"
DB_PATH      = PROJECT_ROOT / "social_listening.db"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=str(ENV_PATH))
except Exception:
    pass

def _make_engine():
    url = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")
    if url and "://" not in url and url.endswith(".db"):
        url = f"sqlite:///{Path(url).resolve().as_posix()}"
    return create_engine(url, future=True)

engine = _make_engine()

# ---------- Regex / Normalización ----------
RE_URL   = re.compile(r"(https?://\S+|www\.\S+)", flags=re.IGNORECASE)
RE_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", flags=re.IGNORECASE)
RE_PHONE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}\b")
EMOJI_PATTERN = re.compile(
    "[" "\U0001F300-\U0001F5FF" "\U0001F600-\U0001F64F" "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F" "\U0001F780-\U0001F7FF" "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF" "\U0001FA00-\U0001FA6F" "\U0001FA70-\U0001FAFF"
    "\u2600-\u26FF" "\u2700-\u27BF" "]",
    flags=re.UNICODE
)

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def clean_text(s: str, keep_emojis: bool = False):
    """Devuelve (texto_clean, emoji_count, removed_urls, removed_emails, removed_phones)."""
    if s is None:
        return "", 0, 0, 0, 0
    emoji_count = len(EMOJI_PATTERN.findall(s))
    cleaned = s if keep_emojis else EMOJI_PATTERN.sub("", s)
    removed_urls   = len(RE_URL.findall(cleaned));   cleaned = RE_URL.sub(" ", cleaned)
    removed_emails = len(RE_EMAIL.findall(cleaned)); cleaned = RE_EMAIL.sub(" ", cleaned)
    removed_phones = len(RE_PHONE.findall(cleaned)); cleaned = RE_PHONE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
    cleaned = strip_accents(cleaned)
    return cleaned, emoji_count, removed_urls, removed_emails, removed_phones

# ---------- Vista staging (FIJA a tus columnas) ----------
def ensure_staging_view():
    """
    Vista staging_comments con columnas exactas:
      - id:      platform_id
      - fecha:   created_at
      - origen:  normalizado desde platform
      - texto:   content
      - url:     post_url
    """
    with engine.begin() as conn:
        cols = {r[1].lower() for r in conn.execute(text("PRAGMA table_info(comments);")).fetchall()}
        required = {"platform", "platform_id", "content", "post_url", "created_at"}
        missing  = required - cols
        if missing:
            raise RuntimeError("La tabla 'comments' no tiene columnas requeridas: " + ", ".join(sorted(missing)))

        conn.execute(text("DROP VIEW IF EXISTS staging_comments"))
        conn.execute(text("""
            CREATE VIEW staging_comments AS
            SELECT
              platform_id           AS id,
              created_at            AS fecha,
              CASE lower(platform)
                WHEN 'facebook'    THEN 'Facebook'
                WHEN 'instagram'   THEN 'Instagram'
                WHEN 'tripadvisor' THEN 'TripAdvisor'
                ELSE platform
              END                   AS origen,
              content               AS texto,
              post_url              AS url
            FROM comments;
        """))

# ---------- Lectura desde la vista ----------
def read_source(limit: int | None) -> pd.DataFrame:
    limit_clause = f" LIMIT {limit}" if limit else ""
    with engine.begin() as conn:
        try:
            return pd.read_sql_query(
                f"SELECT id, fecha, origen, texto, url FROM staging_comments{limit_clause};",
                conn
            )
        except OperationalError:
            ensure_staging_view()
            return pd.read_sql_query(
                f"SELECT id, fecha, origen, texto, url FROM staging_comments{limit_clause};",
                conn
            )

# ---------- Columna de salida en la misma tabla ----------
def ensure_clean_column():
    with engine.begin() as conn:
        cols = {r[1].lower() for r in conn.execute(text("PRAGMA table_info(comments);")).fetchall()}
        if "content_clean" not in cols:
            conn.execute(text("ALTER TABLE comments ADD COLUMN content_clean TEXT"))

# ---------- MAIN ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Procesar máximo N filas")
    ap.add_argument("--keep-emojis", action="store_true", help="Conservar emojis en content_clean")
    ap.add_argument("--reset", action="store_true", help="Poner NULL en content_clean antes de actualizar")
    args = ap.parse_args()

    ensure_staging_view()
    ensure_clean_column()

    if args.reset:
        with engine.begin() as conn:
            conn.execute(text("UPDATE comments SET content_clean=NULL"))

    df = read_source(args.limit)
    if df.empty:
        print("[INFO] No hay filas para procesar en staging_comments.")
        return

    rows = []
    for _, row in df.iterrows():
        cleaned, *_ = clean_text(row["texto"], keep_emojis=args.keep_emojis)
        rows.append({"id": row["id"], "content_clean": cleaned})
    out = pd.DataFrame(rows).drop_duplicates(subset=["id"])

    with engine.begin() as conn:
        tmp = "__clean_tmp"
        out.to_sql(tmp, conn, if_exists="replace", index=False)
        conn.execute(text(f"""
            UPDATE comments
               SET content_clean = (SELECT t.content_clean FROM {tmp} t WHERE t.id = comments.platform_id)
             WHERE EXISTS (SELECT 1 FROM {tmp} t WHERE t.id = comments.platform_id);
        """))
        conn.execute(text(f"DROP TABLE {tmp}"))

    with engine.begin() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM comments WHERE content_clean IS NOT NULL")).scalar_one()
    print(f"[OK] Limpieza completada. Filas con content_clean poblado: {total}")

if __name__ == "__main__":
    main()
