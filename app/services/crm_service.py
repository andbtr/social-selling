from app.models.crm_lead import CRMLead
import requests
from app.models.crm_lead import CRMLead
from app.models.lead_score import LeadScore
from app.models.comment import Comment

class CrmService:
    def __init__(self, crm_api_base_url: str):
        self.crm_api_base_url = crm_api_base_url

    def send_lead(self, lead: CRMLead):
        """
        Sends a lead to the CRM.
        """
        lead_data = {
            "fullName": lead.fullname or lead.author,  # Use fullname if available (from form), else author (from comment)
            "email": lead.email,
            "phone": lead.phone,
            "origin": lead.platform,
            "segment": lead.segment,
            "status": "NUEVO",
            "interest": lead.interest,
            "score": float(lead.lead_score) if lead.lead_score else None,
            "convertedToClient": False,
            "primaryContactChannel": None,  # Not in CRMLead
            "estimatedPotentialValue": None, # Not in CRMLead
            "instagramId": lead.instagram_id,
            "facebookId": lead.facebook_id,
            "tripadvisorId": lead.tripadvisor_id,
            "igUsername": lead.author if lead.platform == "INSTAGRAM" else None,
            "fbUsername": lead.author if lead.platform == "FACEBOOK" else None,
            "tripadvUsername": lead.author if lead.platform == "TRIPADVISOR" else None,
            "commentLink": lead.post_url,
        }

        try:
            response = requests.post(f"{self.crm_api_base_url}/leads", json=lead_data)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, etc.
            print(f"Error sending lead to CRM: {e}")
            return None

    def create_crm_lead_from_comment(self, db, db_comment: Comment, platform: str) -> CRMLead:
        """
        Creates and saves a CRMLead from a Comment and its related LeadScore.
        """
        lead_score = db_comment.lead_score
        crm_lead = CRMLead(
            lead_score_id=lead_score.id if lead_score else None,
            comment_id=db_comment.id,
            priority_level=lead_score.priority_level if lead_score else None,
            lead_score=lead_score.score if lead_score else None,
            author=db_comment.author,
            content=db_comment.content,
            platform=platform,
            post_url=db_comment.post_url,
            fullname=None,
            email=None,
            phone=None,
            segment=None,
            interest=db_comment.content,
            instagram_id=None,
            facebook_id=None,
            tripadvisor_id=None,
        )
        db.add(crm_lead)
        db.commit()
        db.refresh(crm_lead)
        return crm_lead
