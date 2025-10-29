from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.services.meta_auth_service import MetaAuthService
from app.core.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/meta/login", tags=["Meta OAuth"])
async def meta_login():
    """
    Initiates the Meta OAuth2 authentication flow.
    Redirects the user to Meta's authorization URL.
    """
    auth_url = MetaAuthService.get_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/meta/callback", tags=["Meta OAuth"])
async def meta_callback(code: str, state: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Handles the callback from Meta after user authorization.
    Exchanges the authorization code for an access token and stores credentials.
    """
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    token = MetaAuthService.exchange_code_for_token(db, code)
    if not token:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    # Redirect to the status page for a better user experience
    return RedirectResponse(url="/auth/meta/status")


@router.get("/meta/status", tags=["Meta OAuth"])
async def meta_status(db: Session = Depends(get_db)):
    """
    Check if Meta credentials are already stored and valid.
    """
    credentials = MetaAuthService.get_credentials_from_db(db)
    if credentials:
        return {
            "status": "authenticated",
            "fb_page_id": credentials.get("fb_page_id"),
            "ig_business_account_id": credentials.get("ig_business_account_id"),
            "message": "Meta credentials found in database."
        }
    else:
        return {
            "status": "not_authenticated",
            "message": "No Meta credentials found in database. Please visit /auth/meta/login to authenticate."
        }
