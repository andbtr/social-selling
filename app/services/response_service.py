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

        if lead_score.priority_level == "HOT":
            message = f"""Hola {name},

¡Gracias por tu interés! Nos encanta tu comentario y queremos ayudarte lo antes posible.

Un miembro de nuestro equipo se pondrá en contacto contigo en las próximas 2 horas.

¡Esperamos hablar contigo pronto!

Saludos,
Equipo de Atención al Cliente"""

        elif lead_score.priority_level == "WARM":
            message = f"""Hola {name},

Gracias por tu mensaje. Valoramos mucho tu feedback y estamos revisando tu solicitud.

Nos comunicaremos contigo en las próximas 24 horas con más información.

¡Saludos!
Equipo de Atención al Cliente"""

        else:  # COLD
            message = f"""Hola {name},

Agradecemos tu comentario. Hemos registrado tu mensaje en nuestro sistema.

Te contactaremos si necesitamos más información.

¡Gracias!
Equipo de Atención al Cliente"""

        # Add form URL using BASE_URL from config
        form_url = f"{settings.base_url}/crm/form?platform={platform}"
        form_section = f"""

---

📋 **FORMULARIO DE CONTACTO**

Para que podamos contactarte, completa nuestro formulario aquí:
{form_url}

¡Gracias!"""

        return message + form_section
