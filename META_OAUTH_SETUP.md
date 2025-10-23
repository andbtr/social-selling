# Meta OAuth Authentication Setup

Este documento explica cómo usar la autenticación OAuth de Meta para evitar copiar tokens manualmente en el archivo `.env`.

## Requisitos Previos

1. Tener una aplicación registrada en [Meta for Developers](https://developers.facebook.com/)
2. Tener los siguientes valores en tu archivo `.env`:
   - `META_APP_ID`: Tu ID de aplicación Meta
   - `META_APP_SECRET`: Tu secreto de aplicación Meta
   - `META_REDIRECT_URI`: Por defecto es `http://localhost:8000/auth/meta/callback`

## Flujo de Autenticación

### 1. Obtener Credenciales Automáticamente

#### Opción A: Primero Verificar el Estado (Recomendado)

```bash
curl http://localhost:8000/auth/meta/status
```

Respuesta si ya tiene credenciales guardadas:
```json
{
  "status": "authenticated",
  "has_credentials": true,
  "page_id": "123456789",
  "ig_account_id": "987654321"
}
```

Respuesta si NO tiene credenciales guardadas:
```json
{
  "status": "not_authenticated",
  "has_credentials": false,
  "message": "Please visit /auth/meta/login to authenticate"
}
```

#### Opción B: Iniciar el Flujo de Autenticación

1. **Abre tu navegador y ve a:**
   ```
   http://localhost:8000/auth/meta/login
   ```

2. **Serás redirigido a Meta para autorizar la aplicación**
   - Se te pedirá que inicies sesión en tu cuenta de Meta (si no lo has hecho)
   - Se te mostrarán los permisos que la aplicación necesita
   - Haz clic en "Continuar"

3. **Después de autorizar, Meta te redirigirá automáticamente a:**
   ```
   http://localhost:8000/auth/meta/callback?code=<authorization_code>
   ```

4. **El sistema automáticamente:**
   - Intercambiará el código de autorización por un token de acceso
   - Descubrirá tu página de Facebook y cuenta de Instagram
   - Guardará las credenciales en `storage.json`

5. **Verás una respuesta de éxito:**
   ```json
   {
     "message": "Successfully authenticated with Meta",
     "status": "credentials_saved",
     "details": "Your credentials have been securely stored. You can now use the ingestion endpoints."
   }
   ```

### 2. Las Credenciales se Cargan Automáticamente

Una vez guardadas en `storage.json`, las credenciales se cargan automáticamente:

- **Al iniciar la aplicación**, el sistema busca `storage.json`
- **Las credenciales se mapean a las variables de la aplicación:**
  - `user_access_token` → `settings.meta_fb_access_token`
  - `fb_page_id` → `settings.fb_page_id`
  - `ig_business_account_id` → `settings.instagram_business_account_id`

### 3. Verificar Credenciales Guardadas

```bash
# Ver el contenido de las credenciales guardadas
cat storage.json
```

Contenido esperado:
```json
{
    "user_access_token": "EAABla1xZBL8BA...",
    "fb_page_id": "123456789",
    "ig_business_account_id": "987654321"
}
```

## Estructura de Archivos

```
social-selling/
├── storage.json                    # ← Credenciales OAuth guardadas aquí
├── main.py                         # Aplicación principal con nuevo router
├── app/
│   ├── api/
│   │   ├── __init__.py            # Router auth importado aquí
│   │   ├── auth.py                # ← Nuevo: Rutas OAuth
│   │   ├── comments.py
│   │   └── ingestion.py
│   ├── core/
│   │   ├── config.py              # ← Mejorado: Carga credenciales de storage.json
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   └── services/
│       └── meta_auth_service.py   # Ya existía, genera tokens
```

## Variables de Entorno Requeridas

En tu `.env`:

```env
# Meta OAuth Configuration
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_REDIRECT_URI=http://localhost:8000/auth/meta/callback

# Opcional (solo si NO usas OAuth)
# META_FB_ACCESS_TOKEN=your_token
# FB_PAGE_ID=your_page_id
# INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id
```

## Endpoints Disponibles

### GET `/auth/meta/login`
Inicia el flujo OAuth con Meta. Redirige al usuario a Facebook para autorizar.

**Respuesta:**
- Redirección a Meta

### GET `/auth/meta/callback`
Recibe el callback de Meta después de la autorización.

**Parámetros:**
- `code` (string): Código de autorización de Meta
- `state` (string, opcional): Parámetro de estado CSRF

**Respuesta:**
```json
{
  "message": "Successfully authenticated with Meta",
  "status": "credentials_saved",
  "details": "Your credentials have been securely stored. You can now use the ingestion endpoints."
}
```

### GET `/auth/meta/status`
Verifica si hay credenciales OAuth guardadas.

**Respuesta (autenticado):**
```json
{
  "status": "authenticated",
  "has_credentials": true,
  "page_id": "123456789",
  "ig_account_id": "987654321"
}
```

**Respuesta (no autenticado):**
```json
{
  "status": "not_authenticated",
  "has_credentials": false,
  "message": "Please visit /auth/meta/login to authenticate"
}
```

## Flujo Completo Visual

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario abre: http://localhost:8000/auth/meta/login │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ Aplicación redirige a    │
        │ Meta para autorizar      │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │ 2. Usuario autoriza en   │
        │    Meta/Facebook         │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │ Meta redirige a callback con código  │
        │ /auth/meta/callback?code=...         │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │ 3. Intercambiar código por token    │
        │    Descubrir página y IG            │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │ 4. Guardar en storage.json          │
        │    - user_access_token              │
        │    - fb_page_id                     │
        │    - ig_business_account_id         │
        └──────────────┬──────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────────┐
        │ 5. Mostrar mensaje de éxito         │
        │ Credenciales listas para usar       │
        └─────────────────────────────────────┘
```

## Seguridad

- ✅ `storage.json` contiene tus credenciales: **NUNCA** lo compartas o subes a Git
- ✅ Considera agregar `storage.json` a `.gitignore`
- ✅ Los tokens de Meta tienen expiración: se pueden renovar revisitando `/auth/meta/login`

## Troubleshooting

### "No authorization code provided"
- Verifica que viniste desde `/auth/meta/login`
- Asegúrate de autorizar la aplicación en Meta

### "Failed to exchange code for token"
- Verifica que `META_APP_ID` y `META_APP_SECRET` son correctos
- Verifica que `META_REDIRECT_URI` coincide en Meta for Developers

### "Could not find any Facebook Page with a linked Instagram Business Account"
- Tienes que tener una página de Facebook con Instagram Business Account vinculada
- Asegúrate de estar usando una cuenta de administrador de la página

### storage.json no se crea
- Asegúrate de que tienes permisos de escritura en la carpeta del proyecto
- Verifica que la autenticación fue exitosa (revisa los logs)

## Próximos Pasos

1. Verificar que el `storage.json` se creó correctamente
2. Usar los endpoints de ingestion normalmente: `/ingestion/*`
3. Las credenciales se cargarán automáticamente
4. Para renovar tokens, simplemente vuelve a visitar `/auth/meta/login`
