# X API Posting Setup Guide

## 🚀 Quick Start for Tweet Creation

Para poder **crear tweets, responder, retweetear y dar likes** necesitas configurar OAuth 1.0a User Context.

## 📋 Pasos de Configuración

### 1. Obtener Credenciales OAuth

1. Ve a [developer.x.com/en/portal/dashboard](https://developer.x.com/en/portal/dashboard)
2. Selecciona tu **App**
3. Ve a **"Keys and Tokens"**
4. Genera las siguientes credenciales:

   **API Key and Secret:**

   - Click en "Generate" en la sección "Consumer Keys"
   - Guarda tu **API Key** (Consumer Key)
   - Guarda tu **API Secret** (Consumer Secret)

   **Access Token and Secret:**

   - Click en "Generate" en la sección "Authentication Tokens"
   - Guarda tu **Access Token**
   - Guarda tu **Access Token Secret**

⚠️ **IMPORTANTE**: Guarda estas credenciales inmediatamente. No podrás verlas de nuevo.

### 2. Configurar Variables de Entorno

Agrega estas líneas a tu archivo `.env`:

```bash
# X API - Read Operations (ya lo tienes)
X_BEARER_TOKEN=tu_bearer_token_aqui

# X API - Write Operations (nuevas credenciales para posting)
X_API_KEY=tu_api_key_aqui
X_API_SECRET=tu_api_secret_aqui
X_ACCESS_TOKEN=tu_access_token_aqui
X_ACCESS_TOKEN_SECRET=tu_access_token_secret_aqui
```

### 3. Instalar Dependencia

```bash
pip install requests-oauthlib==2.0.0
```

O si estás usando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 4. Verificar Configuración

Inicia el servidor:

```bash
uvicorn main:app --reload
```

Ve a: [http://localhost:8000/docs](http://localhost:8000/docs)

Busca los nuevos endpoints:

- **POST /x/tweets** - Crear tweet
- **DELETE /x/tweets/{tweet_id}** - Eliminar tweet
- **POST /x/retweets** - Retweetear
- **POST /x/likes** - Dar like
- **GET /x/quota** - Ver cuota de posting

## 🎯 Ejemplos de Uso

### Crear un Tweet Simple

```bash
curl -X POST "http://localhost:8000/x/tweets" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¡Hola desde mi API! 🚀"
  }'
```

### Responder a un Tweet

```bash
curl -X POST "http://localhost:8000/x/tweets" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¡Gracias por tu comentario!",
    "reply_to_tweet_id": "1973729560794665200"
  }'
```

### Quote Tweet

```bash
curl -X POST "http://localhost:8000/x/tweets" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¡Totalmente de acuerdo!",
    "quote_tweet_id": "1973729560794665200"
  }'
```

### Crear Tweet con Encuesta

```bash
curl -X POST "http://localhost:8000/x/tweets" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "¿Cuál es tu favorito?",
    "poll_options": ["Opción A", "Opción B", "Opción C"],
    "poll_duration_minutes": 1440
  }'
```

### Retweetear

```bash
curl -X POST "http://localhost:8000/x/retweets" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "TU_USER_ID",
    "tweet_id": "1973729560794665200"
  }'
```

### Dar Like

```bash
curl -X POST "http://localhost:8000/x/likes" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "TU_USER_ID",
    "tweet_id": "1973729560794665200"
  }'
```

### Verificar Cuota

```bash
curl "http://localhost:8000/x/quota"
```

## 📊 Límites del Free Tier

| Acción            | Límite    | Cuenta hacia el límite |
| ----------------- | --------- | ---------------------- |
| Crear tweet       | 1,500/mes | ✅ Sí                  |
| Responder a tweet | 1,500/mes | ✅ Sí                  |
| Quote tweet       | 1,500/mes | ✅ Sí                  |
| Retweetear        | 1,500/mes | ✅ Sí                  |
| Eliminar tweet    | Ilimitado | ❌ No                  |
| Dar like          | Ilimitado | ❌ No                  |
| Quitar like       | Ilimitado | ❌ No                  |
| Quitar retweet    | Ilimitado | ❌ No                  |

**Total de "posts" por mes: 1,500**

## 🔍 Cómo Obtener tu User ID

Tu User ID lo necesitas para retweetear y dar likes.

**Opción 1: Usar la API**

```bash
curl "http://localhost:8000/x/users/by-username/TU_USERNAME"
```

Busca el campo `"id"` en la respuesta.

**Opción 2: Desde X.com**

1. Ve a tu perfil en X.com
2. Inspecciona el HTML
3. Busca `data-user-id` o usa herramientas de desarrollador

## ✅ Verificación Rápida

Prueba que todo funciona:

1. **Health check**:

   ```bash
   curl http://localhost:8000/x/health
   ```

2. **Ver cuota**:

   ```bash
   curl http://localhost:8000/x/quota
   ```

3. **Crear un tweet de prueba**:
   ```bash
   curl -X POST "http://localhost:8000/x/tweets" \
     -H "Content-Type: application/json" \
     -d '{"text": "🧪 Test desde mi API"}'
   ```

## 🐛 Solución de Problemas

### Error: "OAuth 1.0a credentials are required"

**Solución**: Verifica que tienes todas las variables en tu `.env`:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`

### Error: "401 Unauthorized"

**Posibles causas**:

1. Credenciales incorrectas
2. Tokens expirados o revocados
3. App no tiene permisos de escritura

**Solución**:

1. Regenera tus tokens en el Developer Portal
2. Verifica que tu App tenga permisos "Read and Write"

### Error: "Monthly post limit reached"

**Solución**:

- Espera al siguiente mes
- O upgrade a Basic tier ($200/mes) para 10,000 posts/mes

### Error: "403 Forbidden"

**Posibles causas**:

1. Intentando eliminar un tweet de otro usuario
2. Tweet protegido o privado
3. App suspendida

## 📚 Documentación Adicional

- **Guía Completa**: [`X_API_GUIDE.md`](X_API_GUIDE.md)
- **Implementación**: [`X_API_IMPLEMENTATION.md`](X_API_IMPLEMENTATION.md)
- **Tests**: [`test_x_api.py`](test_x_api.py)
- **API Docs (Swagger)**: http://localhost:8000/docs

## 🎉 ¡Todo Listo!

Ahora puedes crear tweets, responder, retweetear y más desde tu API.

Para ver todos los endpoints disponibles, visita:
**http://localhost:8000/docs**

---

**¿Preguntas?** Consulta la [documentación oficial de X API](https://developer.x.com/en/docs/twitter-api)
