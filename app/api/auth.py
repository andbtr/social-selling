from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from app.services.meta_auth_service import MetaAuthService

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
async def meta_callback(code: str = Query(...), state: str = Query(None)):
    """
    Handles the callback from Meta after user authorization.
    Exchanges the authorization code for an access token and stores credentials.
    """
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code provided")
    
    token = MetaAuthService.exchange_code_for_token(code)
    if not token:
        raise HTTPException(status_code=400, detail="Failed to exchange code for token")
    
    # Credentials are automatically saved in storage.json by exchange_code_for_token
    return JSONResponse(
        status_code=200,
        content={
            "message": "Successfully authenticated with Meta",
            "status": "credentials_saved",
            "details": "Your credentials have been securely stored. You can now use the ingestion endpoints."
        }
    )


@router.get("/meta/status", tags=["Meta OAuth"])
async def meta_status():
    """
    Check if Meta credentials are already stored and valid.
    """
    credentials = MetaAuthService.get_credentials()
    if credentials:
        return {
            "status": "authenticated",
            "has_credentials": True,
            "page_id": credentials.get("fb_page_id"),
            "ig_account_id": credentials.get("ig_business_account_id")
        }
    else:
        return {
            "status": "not_authenticated",
            "has_credentials": False,
            "message": "Please visit /auth/meta/login to authenticate"
        }
