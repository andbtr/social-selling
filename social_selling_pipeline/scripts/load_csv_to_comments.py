#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Carga (upsert) de CSV/XLSX a la tabla 'comments'.

- Soporta .csv y .xlsx
- Usa la BD de la RAÍZ del repo (social_listening.db), portable.
- Upsert por PRIMARY KEY (id) usando INSERT OR REPLACE (SQLite).
- Normaliza fechas a 'YYYY-MM-DD HH:MM:SS'.
- Acepta alias de columnas y construye 'id' si falta (usa platform_id).
- Autocompleta fechas:
    * Si created_at está vacío y no usas --no-autofill -> se pone la hora actual.
    * Si platform_created_at está vacío -> se copia de created_at.
"""

import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

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

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    rel = DATABASE_URL[len("sqlite:///"):]
    DATABASE_URL = f"sqlite:///{(PROJECT_ROOT / rel).resolve().as_posix()}"

engine = create_engine(DATABASE_URL, future=True)
print(f"[INFO] DB -> {DATABASE_URL}")

# ---------- UTIL: parseo de fechas ----------
FMTS = [
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
]
def to_iso(x):
    if x is None: return None
    s = str(x).strip()
    if not s: return None
    for f in FMTS:
        try:
            return datetime.strptime(s, f).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    ts = pd.to_datetime(s, errors="coerce")
    if pd.isna(ts):
        ts = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if pd.isna(ts):
        return s
    return ts.strftime("%Y-%m-%d %H:%M:%S")

def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- Mapeo de columnas ----------
ALIASES = {
    "id": ["id"],
    "platform": ["platform", "origen", "source"],
    "platform_id": ["platform_id", "post_id", "page_post_id"],
    "id_comment_platform": ["id_comment_platform", "comment_id", "platform_comment_id"],
    "author": ["author", "user", "username", "name"],
    "content": ["content", "message", "texto", "text", "body"],
    "rating": ["rating", "stars", "score"],
    "post_url": ["post_url", "url", "link", "permalink_url"],
    "created_at": ["created_at", "date", "fecha"],
    "platform_created_at": ["platform_created_at", "post_created_at", "published_at", "fecha_publicacion"],
}

REQUIRED_ANY = ["platform", "platform_id", "content", "post_url"]
OPTIONAL = ["id", "id_comment_platform", "author", "rating", "created_at", "platform_created_at"]

def normalize_columns(df: pd.DataFrame, autofill: bool) -> pd.DataFrame:
    cols_lower = {c.lower(): c for c in df.columns}
    out = pd.DataFrame()
    resolved = {}

    # Resolver alias -> nombre real
    for real, aliases in ALIASES.items():
        for a in aliases:
            if a.lower() in cols_lower:
                resolved[real] = cols_lower[a.lower()]
                break

    # Validar requeridas
    missing = [r for r in REQUIRED_ANY if r not in resolved]
    if missing:
        raise ValueError(f"Faltan columnas requeridas (o sus alias) en el archivo: {missing}")

    # Construir dataframe con columnas reales
    for real in REQUIRED_ANY + OPTIONAL:
        if real in resolved:
            out[real] = df[resolved[real]]
        else:
            out[real] = None

    # Completar id si no viene -> usar platform_id
    out["id"] = out["id"].fillna(out["platform_id"]).astype(str)

    # Normalizar strings básicos
    for c in ["platform", "platform_id", "id_comment_platform", "author", "content", "post_url"]:
        out[c] = out[c].astype(str).str.strip()

    # Normalizar platform
    out["platform_norm"] = out["platform"].str.lower()
    out["platform_norm"] = out["platform_norm"].replace({
        "fb":"facebook", "face":"facebook", "facebook":"facebook",
        "ig":"instagram", "insta":"instagram", "instagram":"instagram",
        "ta":"tripadvisor", "tripadvisor":"tripadvisor"
    })
    out["platform"] = out["platform_norm"].where(out["platform_norm"].notna(), out["platform"].str.lower())
    out = out.drop(columns=["platform_norm"])

    # rating numérica
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce")

    # Fechas a ISO
    out["created_at"] = out["created_at"].apply(to_iso)
    out["platform_created_at"] = out["platform_created_at"].apply(to_iso)

    # ---- Autofill de fechas ----
    if autofill:
        # Si created_at está vacío -> ahora
        mask_created_missing = out["created_at"].isna() | (out["created_at"].astype(str).str.strip() == "")
        out.loc[mask_created_missing, "created_at"] = now_iso()
    # platform_created_at vacío -> copiar created_at (si aún queda vacío y created_at existe)
    mask_pl_missing = out["platform_created_at"].isna() | (out["platform_created_at"].astype(str).str.strip() == "")
    out.loc[mask_pl_missing, "platform_created_at"] = out.loc[mask_pl_missing, "created_at"]

    # Orden final
    return out[[
        "id","platform","platform_id","id_comment_platform","author","content",
        "rating","post_url","created_at","platform_created_at"
    ]]

def load_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        try:
            return pd.read_csv(path)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    elif path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path)
    else:
        raise ValueError("Formato no soportado. Usa .csv o .xlsx")

def ensure_table():
    create_table = """
    CREATE TABLE IF NOT EXISTS comments (
      id INTEGER PRIMARY KEY,
      platform TEXT,
      platform_id TEXT,
      id_comment_platform TEXT,
      author TEXT,
      content TEXT,
      rating REAL,
      post_url TEXT,
      created_at TEXT,
      platform_created_at TEXT
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_table))


def upsert_comments(df: pd.DataFrame):
    ensure_table()
    # opcional: uniformar platform a MAYÚSCULAS para que se vea como tu data actual
    df["platform"] = df["platform"].str.upper()

    with engine.begin() as conn:
        tmp = "__comments_tmp"
        df.to_sql(tmp, conn, if_exists="replace", index=False)

        # INSERT append-only (sin 'id', lo asigna SQLite)
        conn.execute(text("""
            INSERT INTO comments
            (platform, platform_id, id_comment_platform, author, content, rating,
             post_url, created_at, platform_created_at)
            SELECT platform, platform_id, id_comment_platform, author, content, rating,
                   post_url, created_at, platform_created_at
            FROM __comments_tmp;
        """))

        conn.execute(text("DROP TABLE __comments_tmp"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", "-f", required=True, help="Ruta al CSV/XLSX a cargar")
    ap.add_argument("--no-autofill", action="store_true",
                    help="No autocompletar created_at con la hora actual cuando falte")
    args = ap.parse_args()

    src = Path(args.file).expanduser().resolve()
    df_raw = load_file(src)
    print(f"[INFO] Rows leídas: {len(df_raw)}  |  Columnas: {list(df_raw.columns)}")

    df_norm = normalize_columns(df_raw, autofill=not args.no_autofill)
    print(f"[INFO] Rows normalizadas: {len(df_norm)}")

    upsert_comments(df_norm)
    print(f"[OK] Carga completada en 'comments': {len(df_norm)} filas (upsert).")

if __name__ == "__main__":
    main()
