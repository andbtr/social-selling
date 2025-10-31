import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.crm_lead import CRMLead, CRMLeadStatus
from app.models.lead_score import LeadScore
from app.models.comment import Comment

logger = logging.getLogger(__name__)


class CRMService:
    """Service to sync leads with external CRM system."""
    
    # Configure your CRM endpoint here
    CRM_BASE_URL = settings.crm_api_url if hasattr(settings, 'crm_api_url') else "https://api.crm.example.com"
    CRM_API_KEY = settings.crm_api_key if hasattr(settings, 'crm_api_key') else None
    
    @staticmethod
    async def sync_hot_warm_leads(db: Session, limit: int = 50) -> Dict[str, Any]:
        """
        Fetch HOT and WARM leads from LeadScore and sync them to CRM.
        Returns summary of sync results.
        """
        try:
            # Get all HOT and WARM leads that haven't been synced yet
            hot_warm_leads = db.query(LeadScore).filter(
                LeadScore.priority_level.in_(["HOT", "WARM"]),
            ).order_by(LeadScore.score.desc()).limit(limit).all()
            
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
                
                # Get comment details
                comment = db.query(Comment).filter(Comment.id == lead_score.comment_id).first()
                if not comment:
                    logger.warning(f"Comment {lead_score.comment_id} not found for lead score {lead_score.id}")
                    continue
                
                # Prepare lead data for CRM
                lead_data = CRMService._prepare_lead_data(lead_score, comment)
                
                # Send to CRM
                crm_result = await CRMService._send_to_crm(lead_data)
                
                if crm_result["success"]:
                    synced_count += 1
                    # Create or update CRMLead record
                    crm_lead = existing_crm_lead or CRMLead(
                        lead_score_id=lead_score.id,
                        comment_id=comment.id,
                        priority_level=lead_score.priority_level,
                        lead_score=lead_score.score,
                        author=comment.author,
                        content=comment.content,
                        platform=comment.platform,
                        post_url=comment.post_url,
                    )
                    crm_lead.crm_lead_id = crm_result.get("crm_lead_id")
                    crm_lead.crm_status = CRMLeadStatus.SYNCED
                    crm_lead.synced_at = datetime.utcnow()
                    crm_lead.sync_error = None
                    crm_lead.sync_attempts += 1
                    
                    db.add(crm_lead)
                    db.commit()
                    logger.info(f"Successfully synced lead score {lead_score.id} to CRM (ID: {crm_lead.crm_lead_id})")
                else:
                    failed_count += 1
                    # Create or update CRMLead record with error
                    crm_lead = existing_crm_lead or CRMLead(
                        lead_score_id=lead_score.id,
                        comment_id=comment.id,
                        priority_level=lead_score.priority_level,
                        lead_score=lead_score.score,
                        author=comment.author,
                        content=comment.content,
                        platform=comment.platform,
                        post_url=comment.post_url,
                    )
                    crm_lead.crm_status = CRMLeadStatus.FAILED
                    crm_lead.sync_error = crm_result.get("error", "Unknown error")
                    crm_lead.last_sync_attempt = datetime.utcnow()
                    crm_lead.sync_attempts += 1
                    
                    db.add(crm_lead)
                    db.commit()
                    logger.error(f"Failed to sync lead score {lead_score.id}: {crm_result.get('error')}")
            
            return {
                "status": "success",
                "synced": synced_count,
                "failed": failed_count,
                "total": len(hot_warm_leads),
                "message": f"Synced {synced_count} leads, {failed_count} failed"
            }
        
        except Exception as e:
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
        return {
            "priority": lead_score.priority_level.lower(),  # hot or warm
            "score": float(lead_score.score),
            "author": comment.author or "Unknown",
            "content": comment.content,
            "platform": comment.platform,
            "post_url": comment.post_url,
            "rating": comment.rating,
            "sentiment": comment.sentiment,
            "sentiment_confidence": comment.sentiment_confidence,
            "intention": comment.intention,
            "intention_confidence": comment.intention_confidence,
            "created_at": comment.platform_created_at.isoformat() if comment.platform_created_at else None,
        }
    
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

