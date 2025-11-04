import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from app.core.config import settings
from app.models.crm_lead import CRMLead, CRMLeadStatus
from app.models.lead_score import LeadScore
from app.models.comment import Comment

logger = logging.getLogger(__name__)


class CRMService:
    """Service to sync leads with external CRM system."""
    
    # Configure your CRM endpoint here
    CRM_BASE_URL = settings.crm_api_url if hasattr(settings, 'crm_api_url') else "https://api.crm.example.com"

    @staticmethod
    async def sync_hot_warm_leads(db: Session, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch HOT and WARM leads from LeadScore and sync them to CRM.
        Returns summary of sync results.
        """
        try:
            # Get all HOT and WARM leads that haven't been synced yet
            # Use joinedload to efficiently fetch the related comment in one query
            hot_warm_leads = (
                db.query(LeadScore)
                .options(joinedload(LeadScore.comment))
                .filter(LeadScore.priority_level.in_(["HOT", "WARM"]))
                .order_by(LeadScore.score.desc()).limit(limit).all()
            )
            if not hot_warm_leads:
                logger.info("No HOT or WARM leads found to sync")
                return {"status": "success", "synced": 0, "failed": 0, "message": "No leads to sync"}
            
            synced_count = 0
            failed_count = 0
            
            for lead_score in hot_warm_leads:
                # Check if already synced
                existing_crm_lead = db.query(CRMLead).filter(
                    CRMLead.lead_score_id == lead_score.id,
                    CRMLead.crm_status != CRMLeadStatus.FAILED
                ).first()
                
                if existing_crm_lead and existing_crm_lead.crm_status == CRMLeadStatus.SYNCED:
                    logger.debug(f"Lead score {lead_score.id} already synced to CRM")
                    continue
                
                if not lead_score.comment:
                    logger.warning(f"Comment not found for lead score {lead_score.id}")
                    continue
                
                # Prepare lead data for CRM
                lead_data = CRMService._prepare_lead_data(lead_score, lead_score.comment)
                
                # Find or create the CRMLead record before sending the request
                crm_lead = existing_crm_lead or CRMLead(
                    lead_score_id=lead_score.id,
                    comment_id=lead_score.comment.id,
                    priority_level=lead_score.priority_level,
                    lead_score=lead_score.score,
                    author=lead_score.comment.author,
                    content=lead_score.comment.content,
                    platform=lead_score.comment.platform,
                    post_url=lead_score.comment.post_url,
                )
                db.add(crm_lead)
                
                # Send to CRM
                crm_result = await CRMService._send_to_crm(lead_data)
                
                crm_lead.sync_attempts += 1
                crm_lead.last_sync_attempt = datetime.utcnow()

                if crm_result["success"]:
                    synced_count += 1
                    crm_lead.crm_lead_id = crm_result.get("crm_lead_id")
                    crm_lead.crm_status = CRMLeadStatus.SYNCED
                    crm_lead.synced_at = datetime.utcnow()
                    crm_lead.sync_error = None
                    logger.info(f"Successfully synced lead score {lead_score.id} to CRM (ID: {crm_lead.crm_lead_id})")
                else:
                    failed_count += 1
                    crm_lead.crm_status = CRMLeadStatus.FAILED
                    crm_lead.sync_error = crm_result.get("error", "Unknown error")
                    logger.error(f"Failed to sync lead score {lead_score.id}: {crm_result.get('error')}")
            
            db.commit() # Commit all changes at once outside the loop

            return {
                "status": "success",
                "synced": synced_count,
                "failed": failed_count,
                "total": len(hot_warm_leads),
                "message": f"Synced {synced_count} leads, {failed_count} failed"
            }
        
        except Exception as e:
            db.rollback() # Rollback transaction on error
            logger.error(f"Error syncing leads to CRM: {str(e)}")
            return {
                "status": "error",
                "synced": 0,
                "failed": 0,
                "message": f"Sync failed: {str(e)}"
            }
    
    @staticmethod
    def _prepare_lead_data(lead_score: LeadScore, comment: Comment) -> Dict[str, Any]:
        """Prepare lead data in format expected by CRM."""
        
        # NOTE: Assumes you have added `full_name`, `email`, `phone` to your LeadScore model
        # For now, we will use placeholders or data from the comment
        
        payload = {
            "fullName": getattr(lead_score, 'full_name', comment.author),
            "email": getattr(lead_score, 'email', None),
            "phone": getattr(lead_score, 'phone', None),
            "interest": comment.content,
            "score": float(lead_score.score),
            "origin": comment.platform,
            "segment": lead_score.priority_level,
            "instagram_id": None,
            "facebook_id": None,
            "tripadvisor_id": None,
        }

        # Assign platform ID to the correct field in the DTO
        platform_id_str = comment.platform_id
        platform_id_int = int(platform_id_str) if platform_id_str and platform_id_str.isdigit() else None

        if comment.platform == "instagram":
            payload["instagram_id"] = platform_id_int
        elif comment.platform == "facebook":
            payload["facebook_id"] = platform_id_int
        elif comment.platform == "tripadvisor":
            payload["tripadvisor_id"] = platform_id_int
            
        return payload
    
    @staticmethod
    async def _send_to_crm(lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send lead to CRM API endpoint."""
        if not CRMService.CRM_API_KEY:
            logger.warning("CRM_API_KEY not configured")
            return {
                "success": False,
                "error": "CRM API key not configured"
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {CRMService.CRM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{CRMService.CRM_BASE_URL}/leads",
                    json=lead_data,
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "crm_lead_id": data.get("id") or data.get("lead_id"),
                        "crm_response": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"CRM API returned {response.status_code}: {response.text}"
                    }
        
        except httpx.TimeoutException:
            logger.error("Timeout while sending lead to CRM")
            return {
                "success": False,
                "error": "CRM API timeout"
            }
        except Exception as e:
            logger.error(f"Error sending lead to CRM: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_crm_leads_status(db: Session, limit: int = 50) -> Dict[str, Any]:
        """Get status of recently synced leads."""
        crm_leads = db.query(CRMLead).order_by(CRMLead.created_at.desc()).limit(limit).all()
        
        status_summary = {
            "pending": 0,
            "synced": 0,
            "failed": 0,
            "updated": 0
        }
        
        for crm_lead in crm_leads:
            status_summary[crm_lead.crm_status.value] += 1
        
        return {
            "status": "success",
            "summary": status_summary,
            "recent_leads": [
                {
                    "id": cl.id,
                    "crm_lead_id": cl.crm_lead_id,
                    "priority_level": cl.priority_level,
                    "lead_score": float(cl.lead_score),
                    "author": cl.author,
                    "crm_status": cl.crm_status.value,
                    "synced_at": cl.synced_at.isoformat() if cl.synced_at else None,
                    "sync_error": cl.sync_error,
                }
                for cl in crm_leads[:10]
            ]
        }
