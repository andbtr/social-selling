from app.core.config import settings

class CRMResponseService:
    """Service for generating CRM response messages."""

    @staticmethod
    def generate_response_message(lead_score, platform: str = "INSTAGRAM", comment_id: int = None) -> str:
        """
        Generate response message based on lead priority level with form URL.

        Args:
            lead_score: LeadScore model instance
            platform: Platform name (INSTAGRAM or FACEBOOK)
            comment_id: ID of the comment for form reference

        Returns:
            Formatted response message with form URL
        """

        # Add form URL using BASE_URL from config and comment_id
        form_url = f"{settings.base_url}/crm/form?platform={platform}"
        if comment_id:
            form_url += f"&comment_id={comment_id}"

        if lead_score.priority_level == "HOT":
            message = f"""¡Hola! 🙌 Gracias por escribirnos.
        Vimos tu interés y queremos ayudarte de inmediato.

        👉 Completa este breve formulario y te contactamos enseguida:
        {form_url}

        Será un gusto atenderte 🚀"""

        elif lead_score.priority_level == "WARM":
            message = f"""¡Hola! 👋 Gracias por tu mensaje 😊
        Si deseas recibir más información personalizada, puedes completar este breve formulario:

        👉 {form_url}

        Nos comunicaremos contigo apenas lo envíes ✅"""

        else:  # COLD
            message = f"""¡Hola! 👋 Gracias por tu comentario 💬
        Si en algún momento deseas que nos contactemos contigo, puedes completar este formulario:

        👉 {form_url}

        ¡Que tengas un excelente día! 😊"""

        return message

        return message
