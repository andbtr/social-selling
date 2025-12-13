from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.form_response import FormResponseCreate, FormResponseRead
from app.services.form_response_service import FormResponseService
router = APIRouter(prefix="/crm", tags=["CRM"])

@router.get("/form", response_class=HTMLResponse)
async def get_form(
    platform: str = Query("INSTAGRAM", description="Platform: INSTAGRAM or FACEBOOK"),
    comment_id: int | None = Query(None, description="Related comment ID"),
    db: Session = Depends(get_db)
):
    """
    Serve public HTML form for capturing lead information.
    Optional comment_id links the form to the original comment.
    """
    html_form = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Formulario de Contacto</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px; }}
            .container {{ background: white; border-radius: 10px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3); max-width: 500px; width: 100%; padding: 40px; }}
            h1 {{ color: #333; margin-bottom: 10px; font-size: 28px; }}
            .subtitle {{ color: #666; margin-bottom: 30px; font-size: 14px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 8px; color: #333; font-weight: 500; font-size: 14px; }}
            input[type="text"], input[type="email"], input[type="tel"], textarea {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; font-family: inherit; transition: border-color 0.3s; }}
            input[type="text"]:focus, input[type="email"]:focus, input[type="tel"]:focus, textarea:focus {{ outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); }}
            textarea {{ resize: vertical; min-height: 100px; }}
            .checkbox-group {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 30px; }}
            input[type="checkbox"] {{ width: 20px; height: 20px; margin-top: 2px; cursor: pointer; accent-color: #667eea; }}
            .checkbox-group label {{ margin: 0; font-weight: 400; cursor: pointer; color: #555; }}
            .platform-field {{ background: #f5f5f5; padding: 12px; border-radius: 5px; margin-bottom: 20px; }}
            .platform-field label {{ margin-bottom: 5px; }}
            .platform-value {{ color: #667eea; font-weight: 600; font-size: 16px; }}
            button {{ width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }}
            button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }}
            button:active {{ transform: translateY(0); }}
            button[disabled] {{ opacity: 0.55; cursor: not-allowed; box-shadow: none; transform: none; }}
            .success {{ display: none; background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 Formulario de Contacto</h1>
            <p class="subtitle">Completa el formulario. Dejanos tu correo y/o teléfono.</p>
            <div class="success" id="successMessage">
                ✓ ¡Gracias! Tu información ha sido registrada exitosamente.
            </div>
            <form id="contactForm" onsubmit="submitForm(event)">
                <div class="platform-field">
                    <label>Plataforma:</label>
                    <div class="platform-value">{platform}</div>
                    <input type="hidden" name="platform" value="{platform}">
                </div>
                {f'<input type="hidden" name="comment_id" value="{comment_id}">' if comment_id else ''}
                <div class="form-group">
                    <label for="fullname">Nombre Completo *</label>
                    <input type="text" id="fullname" name="fullname" required placeholder="Juan Pérez">
                </div>
                <div class="form-group">
                    <label for="email">Correo Electrónico</label>
                    <input type="email" id="email" name="email" placeholder="tu@correo.com">
                </div>
                <div class="form-group">
                    <label for="phone">Teléfono</label>
                    <input type="tel" id="phone" name="phone" placeholder="+34 600 123 456">
                </div>
                <div class="form-group">
                    <label for="interest">¿Cuál es tu interés?</label>
                    <textarea id="interest" name="interest" placeholder="Cuéntanos más sobre lo que necesitas..."></textarea>
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" id="consent" name="consent" required>
                    <label for="consent">
                        Autorizo el uso de mis datos de contacto para que se comuniquen conmigo
                    </label>
                </div>
                <button type="submit" id="submitBtn" disabled aria-disabled="true">Enviar Información</button>
            </form>
        </div>
        <script>
            // Toggle submit button enabled state based on consent checkbox
            document.addEventListener('DOMContentLoaded', function() {{
                const consentCheckbox = document.getElementById('consent');
                const submitBtn = document.getElementById('submitBtn');
                function toggleButton() {{
                    const enabled = !!consentCheckbox.checked;
                    submitBtn.disabled = !enabled;
                    submitBtn.setAttribute('aria-disabled', submitBtn.disabled ? 'true' : 'false');
                }}
                toggleButton();
                consentCheckbox.addEventListener('change', toggleButton);
            }});

            function hasAtLeastOneContact(email, phone) {{
                const e = (email || '').trim();
                const p = (phone || '').trim();
                return e.length > 0 || p.length > 0;
            }}

            async function submitForm(event) {{
                event.preventDefault();
                // Extra guard: do not submit if consent is not checked
                const consentCheckbox = document.getElementById('consent');
                if (!consentCheckbox.checked) {{ return; }}

                const form = document.getElementById('contactForm');
                const formData = new FormData(form);
                const email = formData.get('email');
                const phone = formData.get('phone');

                // Validate: require email OR phone
                if (!hasAtLeastOneContact(email, phone)) {{
                    alert('Por favor, completa correo o teléfono (al menos uno).');
                    return;
                }}

                const data = {{
                    platform: formData.get('platform'),
                    fullname: formData.get('fullname'),
                    email: email,
                    phone: phone,
                    interest: formData.get('interest'),
                    consent: formData.get('consent') === 'on',
                    comment_id: formData.get('comment_id') ? parseInt(formData.get('comment_id')) : null
                }};
                try {{
                    const response = await fetch('/crm/submit-form', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }});
                    if (response.ok) {{
                        document.getElementById('successMessage').style.display = 'block';
                        form.style.display = 'none';
                    }} else {{
                        const error = await response.json();
                        alert('Error: ' + error.detail);
                    }}
                }} catch (error) {{
                    alert('Error al enviar el formulario: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_form
@router.post("/submit-form", response_model=FormResponseRead)
async def submit_form_response(
    form_data: FormResponseCreate,
    db: Session = Depends(get_db)
):
    """Process form submission from CRM response message."""
    try:
        form_dict = form_data.model_dump()
        crm_lead = FormResponseService.create_crm_lead_from_form(db, form_dict)
        return {
            "id": crm_lead.id,
            "platform": crm_lead.platform,
            "fullname": crm_lead.fullname,
            "email": crm_lead.email,
            "phone": crm_lead.phone,
            "interest": crm_lead.interest,
            "created_at": crm_lead.created_at.isoformat() if crm_lead.created_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing form: {str(e)}")
@router.get("/leads")
async def get_crm_leads(
    platform: str = None,
    db: Session = Depends(get_db)
):
    """Get CRM leads with optional filtering."""
    from app.models.crm_lead import CRMLead
    query = db.query(CRMLead)
    if platform:
        query = query.filter(CRMLead.platform == platform)
    leads = query.order_by(CRMLead.created_at.desc()).all()
    return leads
@router.get("/leads/{lead_id}")
async def get_crm_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific CRM lead."""
    from app.models.crm_lead import CRMLead
    lead = db.query(CRMLead).filter(CRMLead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
