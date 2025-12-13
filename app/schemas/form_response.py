from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import Optional


class FormResponseCreate(BaseModel):
    """Schema for form submission from CRM response."""

    platform: str = Field(..., description="Platform: INSTAGRAM, FACEBOOK, TRIPADVISOR")
    fullname: str = Field(..., min_length=1, description="Full name of the lead")
    email: Optional[EmailStr] = Field(None, description="Email address (optional, provide email or phone)")
    phone: Optional[str] = Field(None, min_length=7, description="Phone number (optional, provide email or phone)")
    interest: Optional[str] = Field(None, description="Interest or message from the user")
    consent: bool = Field(..., description="User consent to be contacted")
    comment_id: Optional[int] = Field(None, description="Related comment ID from social media")

    def model_post_init(self, __context):
        # Enforce at least one of email or phone
        if not self.email and not (self.phone and self.phone.strip()):
            raise ValidationError([
                {
                    'loc': ('email',),
                    'msg': 'Provide at least one contact method: email or phone',
                    'type': 'value_error'
                }
            ], type(self))


class FormResponseRead(BaseModel):
    """Schema for form response read."""

    id: int
    platform: str
    fullname: str
    email: Optional[str]
    phone: Optional[str]
    interest: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
