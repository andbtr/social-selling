from sqlalchemy.orm import Session
from app.models.crm_lead import CRMLead
from app.services.crm_service import CrmService
from app.core.config import settings


class FormResponseService:
    """Service for processing form submissions from CRM responses."""

    @staticmethod
    def create_crm_lead_from_form(db: Session, form_data: dict) -> CRMLead:
        """
        Create a CRMLead from form submission data and sync to external CRM.

        Args:
            db: Database session
            form_data: Form data containing platform, fullname, email, phone, interest, consent

        Returns:
            Created CRMLead object
        """
        try:
            crm_lead = CRMLead(
                platform=form_data.get("platform"),
                fullname=form_data.get("fullname"),
                email=form_data.get("email"),
                phone=form_data.get("phone"),
                interest=form_data.get("interest"),
                # Relations and fields optional for form submissions
            )
            db.add(crm_lead)
            db.commit()
            db.refresh(crm_lead)

            print(f"[FormResponseService] CRMLead from form created: {crm_lead.id}")

            # Try to sync to external CRM if URL is configured
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
            print(f"[FormResponseService] Error creating CRMLead from form: {str(e)}")
            raise

