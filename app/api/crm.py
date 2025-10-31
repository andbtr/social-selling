from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.crm_service import CRMService

router = APIRouter(prefix="/api/crm", tags=["CRM"])


@router.post("/sync-leads")
async def sync_leads_to_crm(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Sync HOT and WARM leads to external CRM system.
    
    This endpoint:
    1. Fetches all HOT and WARM leads from LeadScore
    2. Sends them to the configured CRM endpoint
    3. Tracks sync status in CRMLead table
    
    Returns:
        - synced: number of leads successfully sent to CRM
        - failed: number of leads that failed to sync
        - message: summary of the sync operation
    """
    result = await CRMService.sync_hot_warm_leads(db, limit=limit)
    return result


@router.get("/sync-status")
async def get_sync_status(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get the status of recently synced leads.
    
    Returns:
        - summary: count of leads by sync status (pending, synced, failed, updated)
        - recent_leads: details of the most recent synced leads
    """
    result = CRMService.get_crm_leads_status(db, limit=limit)
    return result


@router.get("/leads")
async def get_crm_leads(
    db: Session = Depends(get_db),
    priority: str = Query(None, enum=["HOT", "WARM"]),
    status: str = Query(None, enum=["pending", "synced", "failed", "updated"]),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Get CRM leads with optional filtering by priority and sync status.
    """
    from app.models.crm_lead import CRMLead, CRMLeadStatus
    
    query = db.query(CRMLead).order_by(CRMLead.created_at.desc())
    
    if priority:
        query = query.filter(CRMLead.priority_level == priority)
    
    if status:
        query = query.filter(CRMLead.crm_status == CRMLeadStatus[status.upper()])
    
    leads = query.limit(limit).all()
    
    return {
        "status": "success",
        "count": len(leads),
        "leads": [
            {
                "id": cl.id,
                "crm_lead_id": cl.crm_lead_id,
                "priority_level": cl.priority_level,
                "lead_score": float(cl.lead_score),
                "author": cl.author,
                "content": cl.content,
                "platform": cl.platform,
                "crm_status": cl.crm_status.value,
                "synced_at": cl.synced_at.isoformat() if cl.synced_at else None,
                "sync_error": cl.sync_error,
            }
            for cl in leads
        ]
    }

