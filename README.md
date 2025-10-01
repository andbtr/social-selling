# Social Listening Platform

Una aplicación de social selling centrada en la fase de social listening, diseñada para ingestar y almacenar comentarios de múltiples plataformas de redes sociales.

## 📋 Características

- **Ingesta de datos multi-plataforma**: Soporte para Meta (Facebook/Instagram), X (Twitter) y TripAdvisor
- **API REST con FastAPI**: Endpoints rápidos y documentados automáticamente
- **Almacenamiento con SQLAlchemy**: Base de datos relacional para gestionar comentarios
- **Arquitectura modular**: Servicios separados para cada plataforma
- **Migraciones de base de datos**: Gestión de esquemas con Alembic

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/andbtr/social-selling.git
cd social-selling
```

2. **Crear entorno virtual**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de API:

```env
DATABASE_URL=sqlite:///./social_listening.db
META_API_KEY=tu_clave_api_meta
X_API_KEY=tu_clave_api_x
TRIPADVISOR_API_KEY=tu_clave_api_tripadvisor
```

5. **Inicializar la base de datos**

```bash
# Opción 1: Con Alembic (recomendado)
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Opción 2: Inicialización automática al iniciar la app
# La base de datos se creará automáticamente al ejecutar la aplicación
```

6. **Ejecutar la aplicación**

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

## 📖 Documentación de la API

### Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principales

#### Health Check

```http
GET /
GET /health
```

#### Gestión de Comentarios

```http
# Crear comentario
POST /comments/

# Listar comentarios
GET /comments/?skip=0&limit=100&platform=meta

# Obtener comentario específico
GET /comments/{comment_id}
```

#### Ingesta de Datos

```http
# Ingestar comentarios de Meta
POST /ingest/meta/{post_id}

# Ingestar respuestas de X (Twitter)
POST /ingest/x/{tweet_id}

# Ingestar reviews de TripAdvisor
POST /ingest/tripadvisor/{location_id}
```

### Ejemplo de Uso

#### Ingestar comentarios de Meta

```bash
curl -X POST "http://localhost:8000/ingest/meta/12345" \
  -H "Content-Type: application/json"
```

#### Listar comentarios filtrados por plataforma

```bash
curl "http://localhost:8000/comments/?platform=meta&limit=10"
```

## 🏗️ Estructura del Proyecto

```
social-selling/
├── alembic/              # Migraciones de base de datos
│   ├── versions/         # Scripts de migración
│   └── env.py
├── app/
│   ├── api/             # Endpoints de la API
│   │   ├── comments.py
│   │   └── ingestion.py
│   ├── core/            # Configuración central
│   │   ├── config.py
│   │   └── database.py
│   ├── models/          # Modelos SQLAlchemy
│   │   └── comment.py
│   ├── schemas/         # Esquemas Pydantic
│   │   └── comment.py
│   └── services/        # Lógica de negocio
│       ├── comment_service.py
│       └── ingestion_service.py
├── main.py              # Punto de entrada de la aplicación
├── requirements.txt     # Dependencias
├── .env.example        # Plantilla de configuración
└── README.md
```

## 🔧 Tecnologías Utilizadas

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy**: ORM para Python
- **Alembic**: Migraciones de base de datos
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI
- **httpx**: Cliente HTTP asíncrono

## 🔌 Integración con APIs

### Meta (Facebook/Instagram)

La integración actual incluye una implementación mock. Para usar la API real:

1. Obtén credenciales en [Meta for Developers](https://developers.facebook.com/)
2. Actualiza `META_API_KEY` y `META_API_SECRET` en `.env`
3. Implementa la llamada real en `app/services/ingestion_service.py`

### X (Twitter)

1. Obtén credenciales en [Twitter Developer Portal](https://developer.twitter.com/)
2. Actualiza las credenciales en `.env`
3. Implementa la llamada real en `app/services/ingestion_service.py`

### TripAdvisor

1. Obtén API key en [TripAdvisor Developer Portal](https://www.tripadvisor.com/developers)
2. Actualiza `TRIPADVISOR_API_KEY` en `.env`
3. Implementa la llamada real en `app/services/ingestion_service.py`

## 🗄️ Base de Datos

### Modelo de Datos

La tabla `comments` almacena:

- `id`: Identificador único
- `platform`: Plataforma de origen (meta, x, tripadvisor)
- `platform_id`: ID único del comentario en la plataforma
- `author`: Autor del comentario
- `content`: Contenido del comentario
- `post_url`: URL del post/comentario
- `created_at`: Fecha de creación en nuestra BD
- `platform_created_at`: Fecha de creación en la plataforma
- `metadata`: JSON con datos adicionales específicos de la plataforma

### Migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

## 🧪 Desarrollo

### Ejecutar en modo desarrollo

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Cambiar a PostgreSQL (Producción)

1. Instalar driver PostgreSQL:
```bash
pip install psycopg2-binary
```

2. Actualizar `DATABASE_URL` en `.env`:
```env
DATABASE_URL=postgresql://usuario:contraseña@localhost/social_listening
```

## 📝 Licencia

MIT License - ver el archivo [LICENSE](LICENSE) para más detalles.
