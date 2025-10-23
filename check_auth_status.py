#!/usr/bin/env python3
"""
Script para verificar el estado de autenticación OAuth con Meta.
Uso: python check_auth_status.py
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


def load_credentials() -> Optional[Dict[str, Any]]:
    """Carga las credenciales de storage.json."""
    storage_path = Path(__file__).parent / "storage.json"
    
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"❌ Error al leer storage.json: {e}")
        return None


def main():
    """Verifica y muestra el estado de autenticación."""
    print("=" * 60)
    print("🔐 Meta OAuth Authentication Status")
    print("=" * 60)
    
    credentials = load_credentials()
    
    if credentials:
        print("\n✅ AUTENTICADO - Credenciales encontradas en storage.json\n")
        print(f"📱 Facebook Page ID:          {credentials.get('fb_page_id', 'N/A')}")
        print(f"📸 Instagram Account ID:      {credentials.get('ig_business_account_id', 'N/A')}")
        print(f"🔑 Access Token (primeros 20): {credentials.get('user_access_token', 'N/A')[:20]}...")
        
        print("\n" + "=" * 60)
        print("✅ Tu aplicación está lista para usar los endpoints:")
        print("   - /api/ingestion/instagram")
        print("   - /api/comments")
        print("=" * 60)
        
    else:
        print("\n❌ NO AUTENTICADO - No hay credenciales guardadas\n")
        print("Para autenticarte:")
        print("  1. Inicia el servidor: python main.py")
        print("  2. Abre en el navegador: http://localhost:8000/auth/meta/login")
        print("  3. Autoriza la aplicación en Meta")
        print("  4. Las credenciales se guardarán automáticamente")
        
        print("\n" + "=" * 60)
        print("Para verificar el estado nuevamente, ejecuta:")
        print("  python check_auth_status.py")
        print("=" * 60)
    
    print()


if __name__ == "__main__":
    main()
