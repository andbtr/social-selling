from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.crm_service import CrmService
from app.models.crm_lead import CRMLead, CRMLeadStatus
from app.models.lead_score import LeadScore
from app.models.comment import Comment
import datetime

router = APIRouter(prefix="/api/crm", tags=["CRM"])

# --- Test Endpoints for Proving Java Integration ---

@router.post("/test/send-by-lead-score-id/{lead_score_id}", tags=["CRM Testing"])
async def test_send_lead_by_lead_score(lead_score_id: int, db: Session = Depends(get_db)):
    """
    Finds a LeadScore, creates/updates a CRMLead record, and sends it to the CRM.
    This is a utility endpoint for easy testing.
    """
    # 1. Find the LeadScore and its associated Comment
    lead_score = db.query(LeadScore).filter(LeadScore.id == lead_score_id).first()
    if not lead_score:
        raise HTTPException(status_code=404, detail=f"LeadScore with id {lead_score_id} not found.")

    comment = db.query(Comment).filter(Comment.id == lead_score.comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail=f"Comment with id {lead_score.comment_id} not found.")

    # 2. Find or create the CRMLead
    crm_lead = db.query(CRMLead).filter(CRMLead.lead_score_id == lead_score_id).first()
    if not crm_lead:
        crm_lead = CRMLead(
            lead_score_id=lead_score.id,
            comment_id=comment.id,
            priority_level=lead_score.priority_level,
            lead_score=lead_score.score,
            author=comment.author,
            content=comment.content,
            platform=comment.platform,
            post_url=comment.post_url,
            crm_status=CRMLeadStatus.PENDING,
            instagram_id=comment.instagram_id,
            facebook_id=comment.facebook_id,
            tripadvisor_id=comment.tripadvisor_id,
        )
        db.add(crm_lead)
    
    # 3. Send to CRM
    crm_service = CrmService(crm_api_base_url="http://localhost:8080/api")
    crm_response = crm_service.send_lead(crm_lead)

    # 4. Update status based on response
    if crm_response and crm_response.get('id'): # Assuming CRM returns a JSON with an 'id'
        crm_lead.crm_status = CRMLeadStatus.SYNCED
        crm_lead.crm_lead_id = str(crm_response.get('id'))
        crm_lead.synced_at = datetime.datetime.utcnow()
        crm_lead.sync_error = None
        db.commit()
        return {"status": "success", "detail": "Lead sent and status updated to SYNCED.", "crm_response": crm_response}
    else:
        crm_lead.crm_status = CRMLeadStatus.FAILED
        crm_lead.sync_error = str(crm_response) # Store the error response
        crm_lead.last_sync_attempt = datetime.datetime.utcnow()
        if crm_lead.sync_attempts is None:
            crm_lead.sync_attempts = 0
        crm_lead.sync_attempts += 1
        db.commit()
        raise HTTPException(status_code=500, detail={"message": "Failed to send lead to CRM.", "crm_error": str(crm_response)})



@router.post("/sync-leads")
async def sync_leads_to_crm(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=500)):
    # ... (original code remains here)
    pass

@router.get("/sync-status")
async def get_sync_status(db: Session = Depends(get_db), limit: int = Query(50, ge=1, le=500)):
    # ... (original code remains here)
    pass

@router.get("/leads")
async def get_crm_leads(db: Session = Depends(get_db), priority: str = Query(None, enum=["HOT", "WARM"]), status: str = Query(None, enum=["pending", "synced", "failed", "updated"]), limit: int = Query(50, ge=1, le=500)):
    # ... (original code remains here)
    pass
