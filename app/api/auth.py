from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.services.meta_auth_service import MetaAuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/meta/auth-url", tags=["Meta OAuth"])
async def get_meta_auth_url():
    """
    Devuelve la URL de autorización de Meta.
    """
    auth_url = MetaAuthService.get_auth_url()
    return {"auth_url": auth_url}


@router.post("/meta/exchange-code", tags=["Meta OAuth"])
async def exchange_meta_code(code: str, db: Session = Depends(get_db)):
    """
    Intercambia el código por dos tokens de larga duración:
    - user_access_token (para acceder a recursos del usuario)
    - page_access_token (para gestionar la página)

    El front llama esto después que Meta redirige con el código.
    """
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")

    token = MetaAuthService.exchange_code_for_token(db, code)
    if not token:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")

    return {
        "status": "success",
        "message": "Both tokens exchanged and stored (user + page long-lived tokens)"
    }


@router.get("/meta/status", tags=["Meta OAuth"])
async def meta_status(db: Session = Depends(get_db)):
    """
    Verifica si hay credenciales Meta guardadas en BD.
    """
    credentials = MetaAuthService.get_credentials_from_db(db)
    if credentials:
        return {
            "authenticated": True,
            "fb_page_id": credentials.get("fb_page_id"),
            "ig_business_account_id": credentials.get("ig_business_account_id"),
            "message": "Meta credentials found in database"
        }
    return {
        "authenticated": False,
        "message": "No Meta credentials found"
    }
