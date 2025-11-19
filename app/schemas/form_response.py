from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class FormResponseCreate(BaseModel):
    """Schema for form submission from CRM response."""

    platform: str = Field(..., description="Platform: INSTAGRAM, FACEBOOK, TRIPADVISOR")
    fullname: str = Field(..., min_length=1, description="Full name of the lead")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., min_length=7, description="Phone number")
    interest: Optional[str] = Field(None, description="Interest or message from the user")
    consent: bool = Field(..., description="User consent to be contacted")
    comment_id: Optional[int] = Field(None, description="Related comment ID from social media")


class FormResponseRead(BaseModel):
    """Schema for form response read."""

    id: int
    platform: str
    fullname: str
    email: str
    phone: str
    interest: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
