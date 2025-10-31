from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base # Ojo: puede ser declarative_base o Base de tu database.py
from datetime import datetime

# Asume que Base está definida en app.core.database o similar
# Si no, puedes definirla aquí: Base = declarative_base()
from app.core.database import Base # Ajusta la importación según tu estructura

class MetaCredentials(Base):
    __tablename__ = "meta_credentials"

    id = Column(Integer, primary_key=True, index=True)
    encrypted_access_token = Column(String, nullable=False)
    encrypted_page_token = Column(String, nullable=True)
    fb_page_id = Column(String, nullable=True)
    ig_business_account_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)