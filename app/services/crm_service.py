from app.models.crm_lead import CRMLead
import requests

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
