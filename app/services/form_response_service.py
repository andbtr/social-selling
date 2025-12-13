from sqlalchemy.orm import Session
from app.models.crm_lead import CRMLead
from app.models.comment import Comment
from app.services.crm_service import CrmService
from app.core.config import settings


class FormResponseService:
    """Service for processing form submissions from CRM responses."""

    @staticmethod
    def create_crm_lead_from_form(db: Session, form_data: dict) -> CRMLead:
        """
        Create a new CRMLead from form submission data and sync to external CRM.
        Each form submission creates a new lead, even if comment_id already has leads.

        Args:
            db: Database session
            form_data: Form data containing platform, fullname, email, phone, interest, consent, comment_id

        Returns:
            Created CRMLead object
        """
        try:
            comment_id = form_data.get("comment_id")
            lead_score_id = None
            post_url = None
            content = None

            # If comment_id is provided, fetch related comment and lead_score
            if comment_id:
                comment = db.query(Comment).filter(Comment.id == comment_id).first()
                if comment:
                    lead_score_id = comment.lead_score.id if comment.lead_score else None
                    post_url = comment.post_url
                    content = comment.content
                    print(f"[FormResponseService] Found comment {comment_id} with lead_score_id: {lead_score_id}")
                else:
                    print(f"[FormResponseService] Comment {comment_id} not found")

            # Always CREATE a new CRMLead (no update behavior)
            print(f"[FormResponseService] Creating new CRMLead for comment {comment_id}")
            crm_lead = CRMLead(
                platform=form_data.get("platform"),
                fullname=form_data.get("fullname"),
                email=form_data.get("email"),
                phone=form_data.get("phone"),
                interest=form_data.get("interest"),
                comment_id=comment_id,
                lead_score_id=lead_score_id,
                post_url=post_url,
                content=content,
            )

            db.add(crm_lead)
            db.commit()
            db.refresh(crm_lead)

            print(f"[FormResponseService] CRMLead {crm_lead.id} saved successfully")

            # Always send lead to external CRM
            if settings.crm_api_url:
                try:
                    crm_service = CrmService(settings.crm_api_url)
                    result = crm_service.send_lead(crm_lead)
                    if result:
                        print(f"[FormResponseService] Lead {crm_lead.id} synced to external CRM")
                    else:
                        print(f"[FormResponseService] Failed to sync lead {crm_lead.id} to external CRM")
                except Exception as sync_error:
                    print(f"[FormResponseService] Error syncing to CRM: {str(sync_error)}")
            else:
                print(f"[FormResponseService] CRM_API_URL not configured, skipping external sync")

            return crm_lead

        except Exception as e:
            db.rollback()
            print(f"[FormResponseService] Error processing form: {str(e)}")
            raise

