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
        from app.core.config import settings

        name = lead_score.comment.author or "Cliente"
        # Add form URL using BASE_URL from config and comment_id
        form_url = f"{settings.base_url}/crm/form?platform={platform}"
        if comment_id:
            form_url += f"&comment_id={comment_id}"

        if lead_score.priority_level == "HOT":
            message = f"""¡Hola {name}! 🙌

            Gracias por tu interés 💬 Nos encantaría ayudarte lo antes posible.

            Por favor completa este breve formulario para ponernos en contacto contigo:
            {form_url}

            🚀 Te contactaremos lo más rápido posible"""

        elif lead_score.priority_level == "WARM":
            message = f"""Hola {name} 👋

            Gracias por tu mensaje 😊 Valoramos mucho tus comentarios.

            Si deseas recibir más información, puedes escribirnos por mensaje directo.
            
            Te responderemos lo más pronto posible"""

        else:  # COLD
            message = f"""Hola {name},

            Gracias por tu comentario 💬 Lo tomaremos en cuenta.

            Si deseas comunicarte con nosotros directamente, puedes escribirnos por mensaje directo.

            ¡Gracias por tomarte el tiempo de escribirnos!"""

        return message
